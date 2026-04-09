import pytest

from api.routes.state import _deep_merge


@pytest.mark.unit
def test_deep_merge_preserves_unsent_fields_and_recurses() -> None:
    base = {
        "hp": {"current": 90, "max": 100},
        "knowledge": {"discipline": 2, "courage": 1},
        "notes": "existing",
    }
    incoming = {
        "hp": {"current": 80},
        "knowledge": {"discipline": 3},
    }

    merged = _deep_merge(base, incoming)

    assert merged["hp"]["current"] == 80
    assert merged["hp"]["max"] == 100
    assert merged["knowledge"]["discipline"] == 3
    assert merged["knowledge"]["courage"] == 1
    assert merged["notes"] == "existing"


@pytest.mark.unit
def test_deep_merge_does_not_overwrite_with_none() -> None:
    base = {"goal": "survive"}
    incoming = {"goal": None}

    merged = _deep_merge(base, incoming)

    assert merged["goal"] == "survive"
