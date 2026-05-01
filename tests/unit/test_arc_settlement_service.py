from __future__ import annotations

from datetime import datetime, timezone

import asyncio

import pytest

from api.models import (
    Arc,
    ArcAPAward,
    ArcBudget,
    ArcRewardEnvelope,
    ArcSettlementResult,
    ArcTimestamps,
    CharacterModel,
    ReputationEntry,
    WorldModel,
)
from api.services.arc_settlement import (
    ArcSettlementApplicationError,
    apply_arc_settlement,
)


def _character(*, ap: int = 0, earned: int = 0, reputation: list[ReputationEntry] | None = None) -> CharacterModel:
    return CharacterModel.model_validate({
        "name": "Sylvara",
        "ancestry": "human",
        "culture": "drakenvale_city",
        "focus": "devoted",
        "background": "soldier",
        "hp": {"current": 100, "max": 100},
        "domains": {"power": 45, "agility": 35, "perception": 35, "endurance": 43, "intellect": 25, "will": 47, "presence": 55},
        "knowledge": {},
        "application": {},
        "fields": {},
        "status_effects": [],
        "notes": "",
        "identity": {"origin": "", "motivations": [], "quirks": [], "bonds": [], "flaws": [], "wound": "", "alignment": {"order": "neutral", "intent": "neutral", "ethos_note": ""}},
        "equipment": {"worn": [], "carried": [], "stashed": []},
        "reputation": [r.model_dump() for r in reputation or []],
        "advancement": {"points_available": ap, "points_spent": 0, "points_earned_total": earned, "tag_counter": 0},
    })


def _world(*, coin: int = 1000, obligations: list[str] | None = None) -> WorldModel:
    return WorldModel.model_validate({
        "location": "test-loc-alpha",
        "threat": "none",
        "goal": "survive",
        "turn": 1,
        "companions": [],
        "companion_archive": [],
        "economy": {"wealth_tier": "modest", "coin": coin, "trade_goods": [], "obligations": obligations or []},
        "politics": {"faction_memberships": [], "active_obligations": [], "legal_standing": "unknown", "known_leverage": [], "active_tensions": [], "conclave_status": "unknown"},
        "time": {"day": 1, "month": "Verdantrise", "year": 847, "time_of_day": "morning", "season": "spring", "festival": None, "weather": "clear", "weather_note": ""},
        "survival": {"hunger": "sated", "hydration": "hydrated", "fatigue": "rested", "load": "normal"},
        "pacing": {"tension": 3, "last_consequence_weight": "local", "turns_since_social_beat": 0, "turns_since_discovery": 0, "turn_count": 1},
    })


def _arc(settlement: ArcSettlementResult | None) -> Arc:
    return Arc(
        id="arc-test",
        session_id="sess-test",
        title="Test Arc",
        summary="A test arc.",
        primary_type="mission_multi_leg",
        subtype="investigation",
        stake_scale="situational",
        origin_type="declared",
        state="ready_to_close",
        budget=ArcBudget(resolved_scene_soft_cap=3, resolved_scene_hard_cap=6, location_soft_cap=1, location_hard_cap=3),
        rewards=ArcRewardEnvelope(ap_award=ArcAPAward(min=0, max=3)),
        settlement=settlement,
        timestamps=ArcTimestamps(created_at=datetime.now(timezone.utc)),
    )


def _settlement(**kwargs) -> ArcSettlementResult:
    data = {
        "arc_id": "arc-test",
        "outcome": "complete",
        "awarded_ap": 0,
        "reputation_changes": [],
        "coin_cd_awarded": 0,
        "coin_cd_forfeit": 0,
        "obligations_added": [],
        "items_awarded": [],
        "leverage_gained": [],
        "settled_at": datetime.now(timezone.utc),
    }
    data.update(kwargs)
    return ArcSettlementResult(**data)


def test_ap_awarded_updates_character_advancement() -> None:
    character, _, events = asyncio.run(apply_arc_settlement(_arc(_settlement(awarded_ap=2)), _character(ap=1, earned=1), _world()))
    assert character.advancement.points_available == 3
    assert character.advancement.points_earned_total == 3
    assert "ap_awarded:arc=arc-test:amount=2" in events


def test_zero_ap_does_not_touch_advancement() -> None:
    character, _, events = asyncio.run(apply_arc_settlement(_arc(_settlement()), _character(ap=1, earned=1), _world()))
    assert character.advancement.points_available == 1
    assert character.advancement.points_earned_total == 1
    assert events == []


def test_reputation_positive_existing_faction() -> None:
    rep = ReputationEntry(faction="House Heartwood", standing=50)
    character, _, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(reputation_changes=[{"faction": "House Heartwood", "delta": 5}])), _character(reputation=[rep]), _world()))
    assert character.reputation[0].standing == 55


def test_reputation_positive_new_faction() -> None:
    character, _, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(reputation_changes=[{"faction": "Greenshields", "delta": 5}])), _character(), _world()))
    assert character.reputation[0].faction == "Greenshields"
    assert character.reputation[0].standing == 5


def test_reputation_negative() -> None:
    rep = ReputationEntry(faction="House Heartwood", standing=50)
    character, _, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(reputation_changes=[{"faction": "House Heartwood", "delta": -10}])), _character(reputation=[rep]), _world()))
    assert character.reputation[0].standing == 40


def test_coin_awarded_updates_world_economy() -> None:
    _, world, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(coin_cd_awarded=500)), _character(), _world(coin=1000)))
    assert world.economy.coin == 1500


def test_coin_forfeit_updates_world_economy() -> None:
    _, world, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(coin_cd_forfeit=300)), _character(), _world(coin=1000)))
    assert world.economy.coin == 700


def test_coin_cannot_go_negative() -> None:
    _, world, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(coin_cd_forfeit=500)), _character(), _world(coin=100)))
    assert world.economy.coin == 0


def test_mixed_coin_awarded_and_forfeit() -> None:
    _, world, events = asyncio.run(apply_arc_settlement(_arc(_settlement(coin_cd_awarded=500, coin_cd_forfeit=200)), _character(), _world(coin=1000)))
    assert world.economy.coin == 1300
    assert "coin_change:arc=arc-test:net=300" in events


def test_obligation_appended() -> None:
    _, world, events = asyncio.run(apply_arc_settlement(_arc(_settlement(obligations_added=[{"type": "favor", "description": "Owe aid"}])), _character(), _world(obligations=[])))
    assert world.economy.obligations == ["Owe aid"]
    assert "obligation_added:arc=arc-test:type=favor" in events


def test_items_emit_consequence_events_without_state_change() -> None:
    character, world, events = asyncio.run(apply_arc_settlement(_arc(_settlement(items_awarded=["item-1", "item-2"])), _character(), _world()))
    assert [e for e in events if e.startswith("item_awarded")] == ["item_awarded:arc=arc-test:item=item-1", "item_awarded:arc=arc-test:item=item-2"]
    assert character == _character()
    assert world == _world()


def test_leverage_emits_consequence_events() -> None:
    _, _, events = asyncio.run(apply_arc_settlement(_arc(_settlement(leverage_gained=["lev-1"])), _character(), _world()))
    assert events == ["leverage_gained:arc=arc-test:leverage=lev-1"]


def test_multiple_change_types_in_single_settlement() -> None:
    character, world, events = asyncio.run(apply_arc_settlement(
        _arc(_settlement(awarded_ap=1, reputation_changes=[{"faction": "Greenshields", "delta": 5}], coin_cd_awarded=100, items_awarded=["item-1"], leverage_gained=["lev-1"])),
        _character(),
        _world(),
    ))
    assert character.advancement.points_available == 1
    assert character.reputation[0].standing == 5
    assert world.economy.coin == 1100
    assert len(events) == 5


def test_empty_settlement_produces_empty_events() -> None:
    _, _, events = asyncio.run(apply_arc_settlement(_arc(_settlement()), _character(), _world()))
    assert events == []


def test_apply_on_arc_without_settlement_raises() -> None:
    with pytest.raises(ArcSettlementApplicationError):
        asyncio.run(apply_arc_settlement(_arc(None), _character(), _world()))


def test_existing_reputation_note_replaced_by_default_note_if_not_in_settlement() -> None:
    rep = ReputationEntry(faction="House Heartwood", standing=50, note="old")
    character, _, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(reputation_changes=[{"faction": "House Heartwood", "delta": 1}])), _character(reputation=[rep]), _world()))
    assert character.reputation[0].note == "Arc settlement: Test Arc"


def test_reputation_last_change_reflects_settlement() -> None:
    character, _, _ = asyncio.run(apply_arc_settlement(_arc(_settlement(reputation_changes=[{"faction": "House Heartwood", "delta": 1}])), _character(), _world()))
    assert "Arc settlement arc-test" in character.reputation[0].last_change
