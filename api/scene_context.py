"""scene_context.py — derive compact GPT-facing scene context from full state."""

from __future__ import annotations

from api.models import (
    CharacterModel,
    LocationData,
    SceneContext,
    SceneLocationSummary,
    SceneRelevantCharacterState,
    WorldModel,
)


def _uniq_limit(values: list[str], limit: int = 8) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for v in values:
        if not v:
            continue
        k = v.strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
        if len(out) >= limit:
            break
    return out


def build_scene_context(
    session_id: str,
    character: CharacterModel,
    world: WorldModel,
    location: LocationData,
    log: list[str],
) -> SceneContext:
    companion_labels = [
        f"{c.name} ({c.status.value})"
        for c in world.companions
        if c.status.value != "departed"
    ]

    visible_entities = _uniq_limit(location.known_npcs + companion_labels)

    immediate_stakes = _uniq_limit(
        [
            f"Goal: {world.goal}" if world.goal else "",
            f"Threat: {world.threat}" if world.threat and world.threat not in {"unknown", "none"} else "",
            f"Legal standing: {world.politics.legal_standing}"
            if world.politics.legal_standing != "unknown"
            else "",
            *world.politics.active_obligations[:2],
        ],
        limit=6,
    )

    active_threats = _uniq_limit(
        [
            world.threat if world.threat not in {"", "unknown", "none"} else "",
            f"Location threat level {location.threat_level}" if location.threat_level > 0 else "",
            *world.politics.active_tensions[:3],
        ],
        limit=6,
    )

    available_opportunities = _uniq_limit(
        [f"Travel to {dest}" for dest in location.connections[:5]],
        limit=6,
    )

    return SceneContext(
        session_id=session_id,
        location_summary=SceneLocationSummary(
            id=location.id,
            name=location.name,
            type=location.type,
            description=location.description,
            tags=location.tags,
        ),
        visible_entities=visible_entities,
        immediate_stakes=immediate_stakes,
        relevant_character_state=SceneRelevantCharacterState(
            name=character.name,
            hp=character.hp,
            status_effects=character.status_effects,
            survival=world.survival,
            active_companions=[c.name for c in world.companions if c.status.value == "active"],
        ),
        recent_log=log[-5:],
        active_threats=active_threats,
        available_opportunities=available_opportunities,
    )
