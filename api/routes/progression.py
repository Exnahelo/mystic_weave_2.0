"""Progression v4.2.0 endpoints: fungible AP, tag advances, and proposals."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from api.database import get_pool
from api.models import (
    APAwardRequest,
    APAwardResponse,
    APSpendRequest,
    APSpendResponse,
    AdvancementState,
    ProgressionStateResponse,
    TagAdvanceRequest,
    TagAdvanceResponse,
    TagConfirmRequest,
    TagConfirmResponse,
    TagProposalRequest,
    TagProposalResponse,
)
from api.progression_math import (
    apply_tag_counter_advance,
    award_for_scale,
    compute_cost,
    normalize_advancement_payload,
    resolve_tag_domain,
    validate_tag_name_format,
)

router = APIRouter(prefix="/progression", tags=["progression"])


def _load_character(row: asyncpg.Record | dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        raise HTTPException(status_code=404, detail="session not found")
    raw = row["character"]
    character = json.loads(raw) if isinstance(raw, str) else raw
    character["advancement"] = normalize_advancement_payload(character.get("advancement"))
    character.setdefault("knowledge", {})
    character.setdefault("application", {})
    character.setdefault("fields", {})
    character.setdefault("pending_tag_proposals", [])
    return character


def _advancement(character: dict[str, Any]) -> AdvancementState:
    return AdvancementState.model_validate(character.get("advancement") or {})


def _tag_block_name(tag_kind: str) -> str:
    return "fields" if tag_kind == "field" else tag_kind


def _pending_responses(character: dict[str, Any]) -> list[TagProposalResponse]:
    return [
        TagProposalResponse(
            proposal_id=p["proposal_id"],
            tag_name=p["tag_name"],
            status="pending",
        )
        for p in character.get("pending_tag_proposals", [])
        if p.get("status") == "pending"
    ]


async def _save_character(conn: asyncpg.Connection, session_id: str, character: dict[str, Any]) -> None:
    await conn.execute(
        "UPDATE game_states SET character = $1::jsonb, updated_at = now() WHERE session_id = $2",
        json.dumps(character),
        session_id,
    )


@router.get("/{session_id}", response_model=ProgressionStateResponse)
async def get_progression(
    session_id: str,
    pool: asyncpg.Pool = Depends(get_pool),
) -> ProgressionStateResponse:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT character FROM game_states WHERE session_id = $1", session_id)
    character = _load_character(row)
    return ProgressionStateResponse(
        advancement=_advancement(character),
        pending_proposals=_pending_responses(character),
        domains=dict(character.get("domains") or {}),
        knowledge=dict(character.get("knowledge") or {}),
        application=dict(character.get("application") or {}),
        fields=dict(character.get("fields") or {}),
    )


@router.post("/{session_id}/tag-advance", response_model=TagAdvanceResponse)
async def tag_advance(
    session_id: str,
    body: TagAdvanceRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> TagAdvanceResponse:
    try:
        resolve_tag_domain(body.tag_name, body.tag_kind, body.domain)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            character = _load_character(row)
            block_name = _tag_block_name(body.tag_kind)
            tags = character.setdefault(block_name, {})
            current_tier = int(tags.get(body.tag_name, 0) or 0)

            if current_tier >= 5:
                return TagAdvanceResponse(
                    tag_name=body.tag_name,
                    tag_kind=body.tag_kind,
                    new_tier=current_tier,
                    at_cap=True,
                    ap_awarded=0,
                    advancement=_advancement(character),
                )

            tags[body.tag_name] = current_tier + 1
            new_advancement, ap_awarded = apply_tag_counter_advance(_advancement(character))
            character["advancement"] = new_advancement.model_dump()
            await _save_character(conn, session_id, character)

    return TagAdvanceResponse(
        tag_name=body.tag_name,
        tag_kind=body.tag_kind,
        new_tier=current_tier + 1,
        at_cap=False,
        ap_awarded=ap_awarded,
        advancement=new_advancement,
    )


@router.post("/{session_id}/ap-award", response_model=APAwardResponse)
async def ap_award(
    session_id: str,
    body: APAwardRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> APAwardResponse:
    ap_awarded = award_for_scale(body.consequence_scale)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            character = _load_character(row)
            advancement = _advancement(character)
            if ap_awarded:
                data = advancement.model_dump()
                data["points_available"] += ap_awarded
                data["points_earned_total"] += ap_awarded
                advancement = AdvancementState.model_validate(data)
                character["advancement"] = advancement.model_dump()
                await _save_character(conn, session_id, character)

    return APAwardResponse(
        ap_awarded=ap_awarded,
        consequence_scale=body.consequence_scale,
        advancement=advancement,
    )


@router.post("/{session_id}/spend", response_model=APSpendResponse)
async def spend_ap(
    session_id: str,
    body: APSpendRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> APSpendResponse:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            character = _load_character(row)
            domains = character.get("domains") or {}
            if body.domain not in domains:
                raise HTTPException(status_code=400, detail="invalid domain")
            current = int(domains[body.domain])
            target = current + body.points_to_add
            try:
                cost = compute_cost(current, target)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

            advancement = _advancement(character)
            if cost > advancement.points_available:
                raise HTTPException(
                    status_code=400,
                    detail=f"insufficient AP: need {cost}, have {advancement.points_available}",
                )

            domains[body.domain] = target
            data = advancement.model_dump()
            data["points_available"] -= cost
            data["points_spent"] += cost
            advancement = AdvancementState.model_validate(data)
            character["domains"] = domains
            character["advancement"] = advancement.model_dump()
            await _save_character(conn, session_id, character)

    return APSpendResponse(
        domain=body.domain,
        new_score=target,
        points_added=body.points_to_add,
        ap_cost=cost,
        advancement=advancement,
    )


@router.post("/{session_id}/propose-tag", response_model=TagProposalResponse)
async def propose_tag(
    session_id: str,
    body: TagProposalRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> TagProposalResponse:
    try:
        validate_tag_name_format(body.tag_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    proposal_id = uuid.uuid4().hex
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            character = _load_character(row)
            character.setdefault("pending_tag_proposals", []).append(
                {
                    "proposal_id": proposal_id,
                    "tag_name": body.tag_name,
                    "tag_kind": body.tag_kind,
                    "domain": body.domain,
                    "justification": body.justification,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "pending",
                }
            )
            await _save_character(conn, session_id, character)

    return TagProposalResponse(proposal_id=proposal_id, tag_name=body.tag_name, status="pending")


@router.post("/{session_id}/confirm-tag", response_model=TagConfirmResponse)
async def confirm_tag(
    session_id: str,
    body: TagConfirmRequest,
    pool: asyncpg.Pool = Depends(get_pool),
) -> TagConfirmResponse:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT character FROM game_states WHERE session_id = $1 FOR UPDATE",
                session_id,
            )
            character = _load_character(row)
            proposals = character.setdefault("pending_tag_proposals", [])
            proposal = next((p for p in proposals if p.get("proposal_id") == body.proposal_id), None)
            if proposal is None:
                raise HTTPException(status_code=404, detail="proposal not found")
            if proposal.get("status") != "pending":
                raise HTTPException(status_code=400, detail="proposal already resolved")

            if body.confirmed:
                block_name = _tag_block_name(proposal["tag_kind"])
                character.setdefault(block_name, {})[proposal["tag_name"]] = 1
                advancement, _ = apply_tag_counter_advance(_advancement(character))
                character["advancement"] = advancement.model_dump()
                proposal["status"] = "committed"
                tier = 1
            else:
                advancement = _advancement(character)
                proposal["status"] = "rejected"
                tier = 0
            proposal["resolved_at"] = datetime.now(timezone.utc).isoformat()
            await _save_character(conn, session_id, character)

    return TagConfirmResponse(
        tag_name=proposal["tag_name"],
        tier=tier,
        advancement=advancement,
    )