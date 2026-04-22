import pytest
from pydantic import ValidationError

from api.companions import (
    BondLinks,
    CreatureCompanion,
    CreatureDomains,
    CreatureNarrative,
    ExceptionalCompanion,
    SapientCompanion,
)
from api.models import Alignment, DomainScores, Equipment, HP, Identity


def _identity() -> Identity:
    return Identity(
        motivations=["Protect the party"],
        alignment=Alignment(order="neutral", intent="good"),
    )


def _equipment() -> Equipment:
    return Equipment()


def _hp() -> HP:
    return HP(current=10, max=10)


def _full_domains() -> DomainScores:
    return DomainScores(
        power=40,
        agility=35,
        perception=45,
        endurance=42,
        intellect=50,
        will=48,
        presence=44,
    )


def _creature_domains() -> CreatureDomains:
    return CreatureDomains(physical=40, instinct=38, composure=35)


def _bond_links() -> BondLinks:
    return BondLinks(primary="char_sylvara")


def _creature_companion(**overrides):
    payload = {
        "name": "Ash",
        "species": "wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["guard"],
        "training_level": "trained",
        "bond_level": "bonded",
        "hp": _hp(),
        "domains": _creature_domains(),
        "bond_links": _bond_links(),
    }
    payload.update(overrides)
    return CreatureCompanion.model_validate(payload)


def _exceptional_companion(**overrides):
    payload = {
        "name": "Whisper",
        "species": "sprite",
        "size": "small",
        "age_category": "adult",
        "tactical_roles": ["scout"],
        "training_level": "expert",
        "bond_level": "bonded",
        "hp": _hp(),
        "bond_links": _bond_links(),
        "exceptional_profile": {
            "sapience": "full",
            "communication": "speech",
            "autonomy": "high",
        },
        "motivations": ["Observe mortals"],
        "domains": _full_domains(),
        "knowledge": {"lore": 2},
        "application": {"illusion_glamour": 1},
        "alignment": {"order": "chaotic", "intent": "good", "ethos_note": ""},
        "known_languages": ["Common"],
    }
    payload.update(overrides)
    return ExceptionalCompanion.model_validate(payload)


@pytest.mark.unit
def test_creature_narrative_empty_is_valid() -> None:
    narrative = CreatureNarrative()
    assert narrative.origin is None
    assert narrative.quirks == []
    assert narrative.drives == []


@pytest.mark.unit
def test_creature_narrative_populated_validates() -> None:
    narrative = CreatureNarrative(
        origin="Raised from a runt in the Feywood.",
        wound="Old scars at shoulder.",
        quirks=["Quiet", "Highly observant"],
        flaws=["Slow to trust strangers"],
        bonds=["Feywood Glade"],
        drives=["Remain with handler", "Hunt when safe"],
    )
    assert narrative.origin.startswith("Raised")
    assert "Quiet" in narrative.quirks


@pytest.mark.unit
def test_creature_narrative_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        CreatureNarrative(origin="test", alignment="lawful_good")


@pytest.mark.unit
def test_creature_companion_minimal_validates() -> None:
    creature = _creature_companion()
    assert creature.name == "Ash"
    assert creature.movement_modes == ["walk"]
    assert creature.natural_weapons == ["none"]


@pytest.mark.unit
def test_creature_companion_narrative_defaults_to_none() -> None:
    creature = _creature_companion()
    assert creature.narrative is None


@pytest.mark.unit
def test_creature_companion_with_narrative_validates() -> None:
    narrative = CreatureNarrative(
        origin="Raised from a runt in the Feywood.",
        quirks=["Quiet", "Observant"],
    )
    creature = _creature_companion(narrative=narrative)
    assert creature.narrative is not None
    assert creature.narrative.origin.startswith("Raised")


@pytest.mark.unit
def test_creature_companion_tactical_roles_list_validates() -> None:
    creature = _creature_companion(tactical_roles=["hunter", "scout"])
    assert creature.tactical_roles == ["hunter", "scout"]


@pytest.mark.unit
def test_creature_companion_empty_tactical_roles_rejected() -> None:
    with pytest.raises(ValidationError):
        _creature_companion(tactical_roles=[])


@pytest.mark.unit
def test_creature_companion_invalid_tactical_role_rejected() -> None:
    with pytest.raises(ValidationError):
        _creature_companion(tactical_roles=["not_a_role"])


@pytest.mark.unit
def test_sapient_companion_minimal_validates() -> None:
    creature = _creature_companion()
    sapient = SapientCompanion.model_validate(
        {
            "name": "Lark",
            "ancestry": "halfling",
            "culture": "riverfolk",
            "background": "scout",
            "focus": "wanderer",
            "hp": _hp(),
            "domains": _full_domains(),
            "identity": _identity(),
            "equipment": _equipment(),
            "bond_links": _bond_links(),
            "companions": [creature],
        }
    )
    assert sapient.name == "Lark"
    assert len(sapient.companions) == 1


@pytest.mark.unit
def test_exceptional_companion_partial_validates() -> None:
    exceptional = ExceptionalCompanion.model_validate(
        {
            "name": "Glimmer",
            "species": "pseudodragon",
            "size": "tiny",
            "age_category": "young_adult",
            "tactical_roles": ["companion"],
            "training_level": "expert",
            "bond_level": "devoted",
            "hp": _hp(),
            "temperament": "curious",
            "bond_links": _bond_links(),
            "exceptional_profile": {
                "sapience": "partial",
                "communication": "symbolic",
                "autonomy": "moderate",
            },
            "motivations": ["Stay near the flame"],
            "domains": _creature_domains(),
        }
    )
    assert exceptional.exceptional_profile.sapience == "partial"


@pytest.mark.unit
def test_exceptional_companion_full_validates() -> None:
    exceptional = _exceptional_companion()
    assert exceptional.exceptional_profile.communication == "speech"
    assert exceptional.known_languages == ["Common"]


@pytest.mark.unit
def test_exceptional_companion_narrative_defaults_to_none() -> None:
    exceptional = _exceptional_companion()
    assert exceptional.narrative is None


@pytest.mark.unit
def test_exceptional_companion_with_narrative_validates() -> None:
    narrative = CreatureNarrative(
        origin="Bound during the oath-rite in the Sacred Pools.",
        drives=["Keep the oath", "Protect the handler"],
    )
    exceptional = _exceptional_companion(narrative=narrative)
    assert exceptional.narrative is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("model_cls", "payload"),
    [
        (
            CreatureCompanion,
            {
                "name": "Ash",
                "species": "wolf",
                "size": "medium",
                "age_category": "adult",
                "tactical_roles": ["guard"],
                "training_level": "trained",
                "bond_level": "bonded",
                "hp": {"current": 10, "max": 10},
                "domains": {"physical": 40, "instinct": 38, "composure": 35},
                "bond_links": {"primary": "char_sylvara"},
                "unexpected": True,
            },
        ),
        (
            SapientCompanion,
            {
                "name": "Lark",
                "ancestry": "halfling",
                "culture": "riverfolk",
                "background": "scout",
                "focus": "wanderer",
                "hp": {"current": 10, "max": 10},
                "domains": _full_domains().model_dump(),
                "identity": _identity().model_dump(),
                "equipment": _equipment().model_dump(),
                "bond_links": {"primary": "char_sylvara"},
                "unexpected": True,
            },
        ),
        (
            ExceptionalCompanion,
            {
                "name": "Whisper",
                "species": "sprite",
                "size": "small",
                "age_category": "adult",
                "tactical_roles": ["scout"],
                "training_level": "expert",
                "bond_level": "bonded",
                "hp": {"current": 10, "max": 10},
                "bond_links": {"primary": "char_sylvara"},
                "exceptional_profile": {
                    "sapience": "full",
                    "communication": "speech",
                    "autonomy": "high",
                },
                "motivations": ["Observe mortals"],
                "domains": _full_domains().model_dump(),
                "knowledge": {"lore": 2},
                "application": {"illusion_glamour": 1},
                "alignment": {"order": "chaotic", "intent": "good", "ethos_note": ""},
                "known_languages": ["Common"],
                "unexpected": True,
            },
        ),
    ],
)
def test_companion_models_forbid_extra_fields(model_cls, payload) -> None:
    with pytest.raises(ValidationError):
        model_cls.model_validate(payload)


@pytest.mark.unit
def test_sapient_companion_allows_creature_nesting_only() -> None:
    sapient = SapientCompanion.model_validate(
        {
            "name": "Lark",
            "ancestry": "halfling",
            "culture": "riverfolk",
            "background": "scout",
            "focus": "wanderer",
            "hp": _hp(),
            "domains": _full_domains(),
            "identity": _identity(),
            "equipment": _equipment(),
            "bond_links": _bond_links(),
            "companions": [_creature_companion()],
        }
    )
    assert sapient.companions[0].species == "wolf"


@pytest.mark.unit
def test_sapient_companion_rejects_nested_sapient_companion() -> None:
    nested = {
        "name": "Nested",
        "ancestry": "elf",
        "culture": "woodland",
        "background": "healer",
        "focus": "sage",
        "hp": {"current": 10, "max": 10},
        "domains": _full_domains().model_dump(),
        "identity": _identity().model_dump(),
        "equipment": _equipment().model_dump(),
        "bond_links": {"primary": "char_nested"},
    }
    with pytest.raises(ValidationError):
        SapientCompanion.model_validate(
            {
                "name": "Lark",
                "ancestry": "halfling",
                "culture": "riverfolk",
                "background": "scout",
                "focus": "wanderer",
                "hp": _hp(),
                "domains": _full_domains(),
                "identity": _identity(),
                "equipment": _equipment(),
                "bond_links": _bond_links(),
                "companions": [nested],
            }
        )


@pytest.mark.unit
def test_sapient_companion_rejects_nested_exceptional_companion() -> None:
    nested = {
        "name": "Whisper",
        "species": "sprite",
        "size": "small",
        "age_category": "adult",
        "tactical_roles": ["scout"],
        "training_level": "expert",
        "bond_level": "bonded",
        "hp": {"current": 10, "max": 10},
        "bond_links": {"primary": "char_sylvara"},
        "exceptional_profile": {
            "sapience": "full",
            "communication": "speech",
            "autonomy": "high",
        },
        "motivations": ["Observe mortals"],
        "domains": _full_domains().model_dump(),
        "knowledge": {"lore": 2},
        "application": {"illusion_glamour": 1},
        "alignment": {"order": "chaotic", "intent": "good", "ethos_note": ""},
        "known_languages": ["Common"],
    }
    with pytest.raises(ValidationError):
        SapientCompanion.model_validate(
            {
                "name": "Lark",
                "ancestry": "halfling",
                "culture": "riverfolk",
                "background": "scout",
                "focus": "wanderer",
                "hp": _hp(),
                "domains": _full_domains(),
                "identity": _identity(),
                "equipment": _equipment(),
                "bond_links": _bond_links(),
                "companions": [nested],
            }
        )


@pytest.mark.unit
def test_exceptional_full_requires_knowledge() -> None:
    with pytest.raises(ValidationError):
        ExceptionalCompanion.model_validate(
            {
                "name": "Whisper",
                "species": "sprite",
                "size": "small",
                "age_category": "adult",
                "tactical_roles": ["scout"],
                "training_level": "expert",
                "bond_level": "bonded",
                "hp": _hp(),
                "bond_links": _bond_links(),
                "exceptional_profile": {
                    "sapience": "full",
                    "communication": "speech",
                    "autonomy": "high",
                },
                "motivations": ["Observe mortals"],
                "domains": _full_domains(),
                "application": {"illusion_glamour": 1},
                "alignment": {"order": "chaotic", "intent": "good", "ethos_note": ""},
                "known_languages": ["Common"],
            }
        )


@pytest.mark.unit
def test_exceptional_full_requires_alignment() -> None:
    with pytest.raises(ValidationError):
        ExceptionalCompanion.model_validate(
            {
                "name": "Whisper",
                "species": "sprite",
                "size": "small",
                "age_category": "adult",
                "tactical_roles": ["scout"],
                "training_level": "expert",
                "bond_level": "bonded",
                "hp": _hp(),
                "bond_links": _bond_links(),
                "exceptional_profile": {
                    "sapience": "full",
                    "communication": "speech",
                    "autonomy": "high",
                },
                "motivations": ["Observe mortals"],
                "domains": _full_domains(),
                "knowledge": {"lore": 2},
                "application": {"illusion_glamour": 1},
                "known_languages": ["Common"],
            }
        )


@pytest.mark.unit
def test_exceptional_full_rejects_creature_domains() -> None:
    with pytest.raises(ValidationError):
        ExceptionalCompanion.model_validate(
            {
                "name": "Whisper",
                "species": "sprite",
                "size": "small",
                "age_category": "adult",
                "tactical_roles": ["scout"],
                "training_level": "expert",
                "bond_level": "bonded",
                "hp": _hp(),
                "bond_links": _bond_links(),
                "exceptional_profile": {
                    "sapience": "full",
                    "communication": "speech",
                    "autonomy": "high",
                },
                "motivations": ["Observe mortals"],
                "domains": _creature_domains(),
                "knowledge": {"lore": 2},
                "application": {"illusion_glamour": 1},
                "alignment": {"order": "chaotic", "intent": "good", "ethos_note": ""},
                "known_languages": ["Common"],
            }
        )


@pytest.mark.unit
def test_exceptional_partial_rejects_full_domain_scores() -> None:
    with pytest.raises(ValidationError):
        ExceptionalCompanion.model_validate(
            {
                "name": "Glimmer",
                "species": "pseudodragon",
                "size": "tiny",
                "age_category": "young_adult",
                "tactical_roles": ["companion"],
                "training_level": "expert",
                "bond_level": "devoted",
                "hp": _hp(),
                "bond_links": _bond_links(),
                "exceptional_profile": {
                    "sapience": "partial",
                    "communication": "symbolic",
                    "autonomy": "moderate",
                },
                "motivations": ["Stay near the flame"],
                "domains": _full_domains(),
            }
        )


@pytest.mark.unit
def test_exceptional_non_speech_rejects_known_languages() -> None:
    with pytest.raises(ValidationError):
        ExceptionalCompanion.model_validate(
            {
                "name": "Glimmer",
                "species": "pseudodragon",
                "size": "tiny",
                "age_category": "young_adult",
                "tactical_roles": ["companion"],
                "training_level": "expert",
                "bond_level": "devoted",
                "hp": _hp(),
                "bond_links": _bond_links(),
                "exceptional_profile": {
                    "sapience": "partial",
                    "communication": "symbolic",
                    "autonomy": "moderate",
                },
                "motivations": ["Stay near the flame"],
                "domains": _creature_domains(),
                "known_languages": ["Common"],
            }
        )


@pytest.mark.unit
def test_bond_links_reject_empty_primary() -> None:
    with pytest.raises(ValidationError):
        BondLinks.model_validate({"primary": "   "})


@pytest.mark.unit
@pytest.mark.parametrize("payload", [{"physical": 24, "instinct": 40, "composure": 35}, {"physical": 40, "instinct": 61, "composure": 35}])
def test_creature_domains_enforce_25_to_60(payload) -> None:
    with pytest.raises(ValidationError):
        CreatureDomains.model_validate(payload)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("training_level", "master"),
        ("bond_level", "friendly"),
        ("age_category", "ancient"),
        ("size", "colossal"),
        ("carrying_capacity", "gigantic"),
    ],
)
def test_literal_enums_reject_invalid_values(field_name, value) -> None:
    payload = {
        "name": "Ash",
        "species": "wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["guard"],
        "training_level": "trained",
        "bond_level": "bonded",
        "hp": {"current": 10, "max": 10},
        "domains": {"physical": 40, "instinct": 38, "composure": 35},
        "bond_links": {"primary": "char_sylvara"},
    }
    payload[field_name] = value
    with pytest.raises(ValidationError):
        CreatureCompanion.model_validate(payload)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("movement_modes", ["teleport"]),
        ("natural_weapons", ["punch"]),
    ],
)
def test_literal_list_enums_reject_invalid_values(field_name, value) -> None:
    payload = {
        "name": "Ash",
        "species": "wolf",
        "size": "medium",
        "age_category": "adult",
        "tactical_roles": ["guard"],
        "training_level": "trained",
        "bond_level": "bonded",
        "hp": {"current": 10, "max": 10},
        "domains": {"physical": 40, "instinct": 38, "composure": 35},
        "bond_links": {"primary": "char_sylvara"},
    }
    payload[field_name] = value
    with pytest.raises(ValidationError):
        CreatureCompanion.model_validate(payload)