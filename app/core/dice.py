import random
from dataclasses import dataclass


@dataclass(frozen=True)
class DiceRoll:
    dice: str
    sides: int
    value: int
    modifier: int
    total: int
    is_critical_success: bool
    is_critical_failure: bool


def parse_dice(dice: str) -> int:
    """
    Converts dice notation like 'd6' or 'd20' to number of sides.
    """
    if not dice.startswith("d"):
        raise ValueError("Dice must use format like 'd6' or 'd20'.")

    sides = int(dice[1:])

    if sides < 2:
        raise ValueError("Dice must have at least 2 sides.")

    return sides


def roll_dice(dice: str = "d20", modifier: int = 0) -> DiceRoll:
    sides = parse_dice(dice)
    value = random.randint(1, sides)
    total = value + modifier

    return DiceRoll(
        dice=dice,
        sides=sides,
        value=value,
        modifier=modifier,
        total=total,
        is_critical_success=value == sides,
        is_critical_failure=value == 1,
    )


def roll_check(
    dice: str = "d20",
    success_threshold: int = 10,
    modifier: int = 0,
) -> dict:
    roll = roll_dice(dice=dice, modifier=modifier)

    return {
        "dice": roll.dice,
        "sides": roll.sides,
        "value": roll.value,
        "modifier": roll.modifier,
        "total": roll.total,
        "success_threshold": success_threshold,
        "success": roll.total >= success_threshold,
        "is_critical_success": roll.is_critical_success,
        "is_critical_failure": roll.is_critical_failure,
    }