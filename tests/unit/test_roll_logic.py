import pytest

from api.routes.roll import _degree_of_success


@pytest.mark.unit
def test_degree_of_success_critical_overrides() -> None:
    assert _degree_of_success(1, 50) == "critical_success"
    assert _degree_of_success(100, 50) == "critical_failure"


@pytest.mark.unit
def test_degree_of_success_bands() -> None:
    assert _degree_of_success(25, 50) == "strong_success"
    assert _degree_of_success(45, 50) == "success"
    assert _degree_of_success(58, 50) == "partial_failure"
    assert _degree_of_success(80, 50) == "failure"
