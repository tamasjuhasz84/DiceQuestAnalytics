"""Unit tests for combat mechanics."""

from app.core.combat import (
    CombatResult,
    Fighter,
    attack,
    calculate_damage,
    run_combat,
)
from app.core.dice import DiceRoll


def test_calculate_damage_has_minimum_one() -> None:
    assert calculate_damage(attack_total=1, defender_defense=10) == 1


def test_attack_updates_defender_hp(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.core.combat.roll_dice",
        lambda *_args, **_kwargs: DiceRoll("d6", 6, 4, 0, 4, False, False),
    )

    attacker = Fighter(id="p", name="Player", hp=20, attack=3, defense=2)
    defender = Fighter(id="e", name="Enemy", hp=10, attack=2, defense=1)

    round_data = attack(attacker, defender, round_number=1)

    assert round_data.round_number == 1
    assert round_data.attacker == "Player"
    assert round_data.defender == "Enemy"
    assert round_data.roll == 4
    assert round_data.total == 7
    assert round_data.damage == 6
    assert defender.hp == 4


def test_run_combat_returns_winner_and_rounds(monkeypatch) -> None:
    # Deterministic roll for both attacker/defender turns.
    monkeypatch.setattr(
        "app.core.combat.roll_dice",
        lambda *_args, **_kwargs: DiceRoll("d6", 6, 6, 0, 6, True, False),
    )

    player = Fighter(id="player", name="Player", hp=14, attack=4, defense=2)
    enemy = Fighter(id="enemy", name="Goblin", hp=8, attack=2, defense=1)

    result: CombatResult = run_combat(player, enemy)

    assert result.winner in {"Player", "Goblin"}
    assert result.loser in {"Player", "Goblin"}
    assert result.winner != result.loser
    assert len(result.rounds) >= 1
