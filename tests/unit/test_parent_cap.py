"""Parent-cap enforcement on the v5 nested knowledge/magic record models.

Brief 13 collapsed the old `validate_application_parent_cap` runtime check
into a structural model_validator on KnowledgeGroupRecord and MagicFieldRecord.
Construction fails immediately if any nested child tier exceeds its parent.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.models import KnowledgeGroupRecord, MagicFieldRecord


@pytest.mark.unit
def test_knowledge_group_application_within_parent_tier_passes() -> None:
    KnowledgeGroupRecord(tier=2, applications={"hauling": 1, "climbing": 2})


@pytest.mark.unit
def test_knowledge_group_rejects_application_above_tier() -> None:
    with pytest.raises(ValidationError, match="exceeds parent group tier"):
        KnowledgeGroupRecord(tier=1, applications={"hauling": 2})


@pytest.mark.unit
def test_knowledge_group_rejects_application_tier_out_of_range() -> None:
    with pytest.raises(ValidationError, match="out of range"):
        KnowledgeGroupRecord(tier=5, applications={"hauling": 6})


@pytest.mark.unit
def test_knowledge_group_empty_applications_allowed() -> None:
    record = KnowledgeGroupRecord(tier=3)
    assert record.applications == {}


@pytest.mark.unit
def test_magic_field_spell_within_field_tier_passes() -> None:
    MagicFieldRecord(tier=3, spells={"seedwake": 1, "barkskin": 3})


@pytest.mark.unit
def test_magic_field_rejects_spell_above_tier() -> None:
    with pytest.raises(ValidationError, match="exceeds parent field tier"):
        MagicFieldRecord(tier=2, spells={"seedwake": 3})


@pytest.mark.unit
def test_magic_field_rejects_spell_tier_out_of_range() -> None:
    with pytest.raises(ValidationError, match="out of range"):
        MagicFieldRecord(tier=5, spells={"seedwake": 0})


@pytest.mark.unit
def test_magic_field_empty_spells_allowed() -> None:
    record = MagicFieldRecord(tier=4)
    assert record.spells == {}
