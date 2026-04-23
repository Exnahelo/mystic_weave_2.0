"""
routes/combat.py — Combat v1.0 stateless resolution endpoints.

Computes pre-combat max HP from armor/shield catalog values and resolves
single attacks using backend-authoritative dice rolls.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.game_data import (
    compute_max_hp,
    get_ammunition,
    get_armor,
    get_shield,
    get_weapon,
    resolve_attack,
)
from api.models import (
    ComputeMaxHpRequest,
    ComputeMaxHpResponse,
    ResolveAttackRequest,
    ResolveAttackResponse,
)

router = APIRouter(prefix="/combat", tags=["combat"])


@router.post(
    "/compute_max_hp",
    response_model=ComputeMaxHpResponse,
    description="Compute pre-combat HP from armor and shield catalog values plus skill tiers.",
)
async def compute_max_hp_endpoint(body: ComputeMaxHpRequest) -> ComputeMaxHpResponse:
    try:
        armor_entry = get_armor(body.armor_id)
        if "armor_floor" not in armor_entry or "armor_ceiling" not in armor_entry:
            raise ValueError("armor_id must reference a full armor set")

        shield_entry = None
        if body.shield_id is not None:
            shield_entry = get_shield(body.shield_id)
            if "armor_floor" not in shield_entry or "armor_ceiling" not in shield_entry:
                raise ValueError("shield_id must reference a valid shield entry")

        computed = compute_max_hp(armor_entry, body.armor_tier, shield_entry, body.shield_tier)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ComputeMaxHpResponse(
        **computed,
        armor_id=body.armor_id,
        armor_tier=body.armor_tier,
        shield_id=body.shield_id,
        shield_tier=body.shield_tier,
    )


@router.post(
    "/resolve_attack",
    response_model=ResolveAttackResponse,
    description="Resolve a single Combat v1.0 attack atomically using backend-authoritative dice.",
)
async def resolve_attack_endpoint(body: ResolveAttackRequest) -> ResolveAttackResponse:
    try:
        weapon_entry = get_weapon(body.weapon_id)
        if "base_damage" not in weapon_entry:
            raise ValueError("weapon_id must reference a weapon with base_damage")
        if body.ammo_id is not None:
            ammo_entry = get_ammunition(body.ammo_id)
            if "damage_modifier" not in ammo_entry:
                raise ValueError("ammo_id must reference ammunition with damage_modifier")

        resolved = resolve_attack(
            weapon_id=body.weapon_id,
            weapon_tier=body.weapon_tier,
            ammo_id=body.ammo_id,
            use_off_hand=body.use_off_hand,
            defender_is_unarmored=body.defender_is_unarmored,
            defender_unarmored_tier=body.defender_unarmored_tier,
            defender_agility_tier=body.defender_agility_tier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ResolveAttackResponse.model_validate(resolved)