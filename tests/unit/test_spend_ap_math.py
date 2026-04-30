import pytest

from api.routes.advancement import _bracket_cost, _total_cost


@pytest.mark.unit
def test_bracket_cost_values() -> None:
    assert _bracket_cost(50) == 1
    assert _bracket_cost(60) == 2
    assert _bracket_cost(70) == 3
    assert _bracket_cost(79) == 3


@pytest.mark.unit
def test_total_cost_crosses_brackets() -> None:
    assert _total_cost(59, 3) == 5
    assert _total_cost(69, 3) == 8


@pytest.mark.unit
def test_total_cost_single_bracket() -> None:
    assert _total_cost(30, 5) == 5


@pytest.mark.unit
def test_total_cost_crosses_60_61() -> None:
    assert _total_cost(58, 5) == 8


@pytest.mark.unit
def test_total_cost_crosses_70_71() -> None:
    assert _total_cost(68, 5) == 13


@pytest.mark.unit
def test_total_cost_rejects_above_cap() -> None:
    with pytest.raises(ValueError, match="above cap"):
        _total_cost(78, 4)