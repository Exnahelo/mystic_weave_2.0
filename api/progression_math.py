"""Pure helpers for progression v4.2.0."""

from __future__ import annotations

import re

from api.game_data import get_tag_primary_domain
from api.models import AdvancementState, DOMAIN_KEYS

VALID_DOMAINS = set(DOMAIN_KEYS)
CONSEQUENCE_AP = {"local": 0, "situational": 1, "regional": 2, "campaign": 4}
TAG_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def compute_cost(current_score: int, target_score: int) -> int:
    """Return AP cost to raise a domain from current_score to target_score."""
    if target_score > 80:
        raise ValueError("would exceed domain cap of 80")
    if target_score <= current_score:
        return 0

    cost = 0
    for new_score in range(current_score + 1, target_score + 1):
        if 25 <= new_score <= 60:
            cost += 1
        elif 61 <= new_score <= 70:
            cost += 2
        elif 71 <= new_score <= 80:
            cost += 3
        else:
            raise ValueError("score below 25 not supported")
    return cost


def award_for_scale(scale: str) -> int:
    try:
        return CONSEQUENCE_AP[scale]
    except KeyError as exc:
        raise ValueError(f"unknown consequence scale: {scale!r}") from exc


def apply_tag_counter_advance(advancement: AdvancementState) -> tuple[AdvancementState, int]:
    """Increment tag_counter once and convert rollover into fungible AP."""
    data = advancement.model_dump()
    data["tag_counter"] += 1
    ap_awarded = 0
    if data["tag_counter"] >= 3:
        data["tag_counter"] -= 3
        data["points_available"] += 1
        data["points_earned_total"] += 1
        ap_awarded = 1
    return AdvancementState.model_validate(data), ap_awarded


def resolve_tag_domain(tag_name: str, tag_kind: str, provided_domain: str | None = None) -> str:
    """Resolve a tag's primary domain from registry, or require a valid explicit domain."""
    registry_domain = get_tag_primary_domain(tag_name, tag_kind)
    if registry_domain:
        return registry_domain
    if provided_domain is None:
        raise ValueError("domain is required for non-canonical tags")
    if provided_domain not in VALID_DOMAINS:
        raise ValueError(f"invalid domain: {provided_domain!r}")
    return provided_domain


def validate_tag_name_format(tag_name: str) -> None:
    if not TAG_NAME_RE.fullmatch(tag_name) or "/" in tag_name or "\\" in tag_name:
        raise ValueError("tag_name must be snake_case with no whitespace or path separators")


def normalize_advancement_payload(payload: dict | None) -> dict:
    """Normalize legacy or missing advancement payloads into v4.2.0 shape."""
    old = payload or {}
    if "points_available" in old and "tag_counter" in old:
        return AdvancementState.model_validate(old).model_dump()

    points_spent = int(old.get("points_spent", 0) or 0)
    points_earned_total = old.get("points_earned_total")
    if points_earned_total is None:
        earned = old.get("points_available_earned") or {}
        points_earned_total = sum(int(v or 0) for v in earned.values()) + points_spent
    points_earned_total = int(points_earned_total or 0)
    return AdvancementState(
        points_available=max(points_earned_total - points_spent, 0),
        points_spent=points_spent,
        points_earned_total=points_earned_total,
        tag_counter=0,
    ).model_dump()