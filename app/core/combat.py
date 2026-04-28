from dataclasses import dataclass, field

from app.core.dice import roll_dice


@dataclass
class Fighter:
    id: str
    name: str
    hp: int
    attack: int
    defense: int


@dataclass
class CombatRound:
    round_number: int
    attacker: str
    defender: str
    roll: int
    modifier: int
    total: int
    damage: int
    defender_hp_after: int


@dataclass
class CombatResult:
    winner: str
    loser: str
    rounds: list[CombatRound] = field(default_factory=list)


def calculate_damage(attack_total: int, defender_defense: int) -> int:
    damage = attack_total - defender_defense
    return max(1, damage)


def attack(attacker: Fighter, defender: Fighter, round_number: int) -> CombatRound:
    roll = roll_dice("d6")
    total = roll.value + attacker.attack
    damage = calculate_damage(total, defender.defense)

    defender.hp = max(0, defender.hp - damage)

    return CombatRound(
        round_number=round_number,
        attacker=attacker.name,
        defender=defender.name,
        roll=roll.value,
        modifier=attacker.attack,
        total=total,
        damage=damage,
        defender_hp_after=defender.hp,
    )


def run_combat(player: Fighter, enemy: Fighter) -> CombatResult:
    rounds: list[CombatRound] = []
    round_number = 1

    while player.hp > 0 and enemy.hp > 0:
        player_round = attack(player, enemy, round_number)
        rounds.append(player_round)

        if enemy.hp <= 0:
            return CombatResult(
                winner=player.name,
                loser=enemy.name,
                rounds=rounds,
            )

        enemy_round = attack(enemy, player, round_number)
        rounds.append(enemy_round)

        if player.hp <= 0:
            return CombatResult(
                winner=enemy.name,
                loser=player.name,
                rounds=rounds,
            )

        round_number += 1

    return CombatResult(
        winner=player.name if player.hp > 0 else enemy.name,
        loser=enemy.name if player.hp > 0 else player.name,
        rounds=rounds,
    )
