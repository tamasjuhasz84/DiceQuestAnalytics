"""Unit tests for dice utilities."""

import pytest

from app.core.dice import parse_dice, roll_check, roll_dice


def test_parse_dice_valid() -> None:
    assert parse_dice("d20") == 20


@pytest.mark.parametrize("value", ["20", "dx", "d1"])
def test_parse_dice_invalid(value: str) -> None:
    with pytest.raises((ValueError, TypeError)):
        parse_dice(value)  # type: ignore[arg-type]


def test_roll_dice_range_and_total(monkeypatch) -> None:
    monkeypatch.setattr("app.core.dice.random.randint", lambda _a, _b: 7)
    roll = roll_dice("d20", modifier=3)

    assert roll.dice == "d20"
    assert roll.sides == 20
    assert roll.value == 7
    assert roll.total == 10


def test_roll_check_success_structure(monkeypatch) -> None:
    monkeypatch.setattr("app.core.dice.random.randint", lambda _a, _b: 10)
    result = roll_check(dice="d20", success_threshold=12, modifier=3)

    assert result["dice"] == "d20"
    assert result["value"] == 10
    assert result["modifier"] == 3
    assert result["total"] == 13
    assert result["success_threshold"] == 12
    assert result["success"] is True
