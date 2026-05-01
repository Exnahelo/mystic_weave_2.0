"""
Arc settlement integration.

Translates a settled arc into actual game state changes by calling existing
progression, reputation, and economy mutation paths. Per Arc System v1
locked design, this code does not reimplement those paths — it orchestrates
existing mutations.

Tag advancement is intentionally NOT processed here. Tag advances are
scene-bound (resolved per-scene during play) and independent of arc
settlement. Emergent arcs that earn zero AP still produce tag advancement
through their resolved scenes.
"""

from __future__ import annotations

from typing import Any

from api.models import Arc, CharacterModel, ReputationEntry, WorldModel


class ArcSettlementApplicationError(Exception):
    """Raised when settlement cannot be applied due to state inconsistency."""


async def apply_arc_settlement(
    arc: Arc,
    character: CharacterModel,
    world: WorldModel,
) -> tuple[CharacterModel, WorldModel, list[str]]:
    """
    Apply an arc's settlement to character and world state.

    Returns the updated (character, world, consequence_events) tuple.
    The caller is responsible for persisting the updated state.
    """
    if arc.settlement is None:
        raise ArcSettlementApplicationError(
            f"Arc {arc.id} has no settlement to apply"
        )

    settlement = arc.settlement
    consequence_events: list[str] = []

    if settlement.awarded_ap > 0:
        character = _apply_ap_award(character, settlement.awarded_ap, arc.id)
        consequence_events.append(
            f"ap_awarded:arc={arc.id}:amount={settlement.awarded_ap}"
        )

    for rep_change in settlement.reputation_changes:
        faction = rep_change.get("faction")
        delta = rep_change.get("delta", 0)
        note = rep_change.get("note", f"Arc settlement: {arc.title}")
        if faction is None or delta == 0:
            continue
        character = _apply_reputation_change(character, faction, delta, note, arc.id)
        consequence_events.append(
            f"reputation_change:arc={arc.id}:faction={faction}:delta={delta}"
        )

    if settlement.coin_cd_awarded > 0 or settlement.coin_cd_forfeit > 0:
        net_coin = settlement.coin_cd_awarded - settlement.coin_cd_forfeit
        if net_coin != 0:
            world = _apply_coin_change(world, net_coin, arc.id)
            consequence_events.append(f"coin_change:arc={arc.id}:net={net_coin}")

    for obligation in settlement.obligations_added:
        world = _apply_obligation(world, obligation, arc.id)
        consequence_events.append(
            f"obligation_added:arc={arc.id}:type={obligation.get('type', 'unknown')}"
        )

    for item_id in settlement.items_awarded:
        consequence_events.append(f"item_awarded:arc={arc.id}:item={item_id}")
    for leverage_id in settlement.leverage_gained:
        consequence_events.append(
            f"leverage_gained:arc={arc.id}:leverage={leverage_id}"
        )

    return character, world, consequence_events


def _apply_ap_award(
    character: CharacterModel,
    amount: int,
    arc_id: str,
) -> CharacterModel:
    """Apply AP award to character using the fungible advancement fields."""
    new_advancement = character.advancement.model_copy(update={
        "points_available": character.advancement.points_available + amount,
        "points_earned_total": character.advancement.points_earned_total + amount,
    })
    return character.model_copy(update={"advancement": new_advancement})


def _apply_reputation_change(
    character: CharacterModel,
    faction: str,
    delta: int,
    note: str,
    arc_id: str,
) -> CharacterModel:
    """Apply a reputation delta, updating an existing entry or creating one."""
    new_reputation = list(character.reputation)
    last_change = f"Arc settlement {arc_id}: {note}"

    for idx, entry in enumerate(new_reputation):
        if entry.faction == faction:
            data = entry.model_dump()
            data.update({
                "standing": entry.standing + delta,
                "note": note,
                "last_change": last_change,
            })
            new_reputation[idx] = ReputationEntry.model_validate(data)
            break
    else:
        new_reputation.append(
            ReputationEntry(
                faction=faction,
                standing=delta,
                note=note,
                last_change=last_change,
            )
        )

    return character.model_copy(update={"reputation": new_reputation})


def _apply_coin_change(
    world: WorldModel,
    delta: int,
    arc_id: str,
) -> WorldModel:
    """Apply a net coin change to world economy."""
    new_coin = max(0, world.economy.coin + delta)
    new_economy = world.economy.model_copy(update={"coin": new_coin})
    return world.model_copy(update={"economy": new_economy})


def _apply_obligation(
    world: WorldModel,
    obligation: dict[str, Any],
    arc_id: str,
) -> WorldModel:
    """Append an obligation to world.economy.obligations."""
    new_obligations = list(world.economy.obligations)
    # The current Economy model stores obligations as strings, so serialize
    # structured settlement obligations into a compact narrator-readable note.
    obligation_text = obligation.get("description") or obligation.get("note") or str(obligation)
    new_obligations.append(obligation_text)
    new_economy = world.economy.model_copy(update={"obligations": new_obligations})
    return world.model_copy(update={"economy": new_economy})