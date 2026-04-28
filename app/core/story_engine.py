import random
from pathlib import Path
from typing import Any

import yaml

from app.core.combat import Fighter, run_combat
from app.core.dice import roll_check


class StoryEngine:
    def __init__(
        self,
        story_path: str = "data/story.yaml",
        locale_path: str = "data/i18n/hu.yaml",
    ) -> None:
        self.story = self._load_yaml(story_path)
        self.translations = self._load_yaml(locale_path)

    def _load_yaml(self, path: str) -> dict[str, Any]:
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

        with file_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML structure in {file_path}")

        return data

    def translate(self, key: str) -> str:
        parts = key.split(".")
        value: Any = self.translations

        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return key
            value = value[part]

        return str(value)

    def get_start_scene_id(self) -> str:
        return self.story["start_scene"]

    def get_scene(self, scene_id: str) -> dict[str, Any]:
        scenes = self.story.get("scenes", {})

        if scene_id not in scenes:
            raise KeyError(f"Scene not found: {scene_id}")

        scene = scenes[scene_id]

        return {
            "id": scene_id,
            "type": scene.get("type"),
            "title": self.translate(scene.get("title_key", "")),
            "text": self.translate(scene.get("text_key", "")),
            "choices": self._translate_choices(scene.get("choices", [])),
            "raw": scene,
        }

    def _translate_choices(self, choices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": choice["id"],
                "label": self.translate(choice["label_key"]),
                "next_scene": choice["next_scene"],
            }
            for choice in choices
        ]

    def choose(self, current_scene_id: str, choice_id: str) -> dict[str, Any]:
        current_scene = self.story["scenes"].get(current_scene_id)

        if not current_scene:
            raise KeyError(f"Scene not found: {current_scene_id}")

        for choice in current_scene.get("choices", []):
            if choice["id"] == choice_id:
                return self.get_scene(choice["next_scene"])

        raise ValueError(
            f"Choice '{choice_id}' not found in scene '{current_scene_id}'"
        )

    def resolve_scene(
        self,
        scene_id: str,
        player_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        player_state = player_state or self.get_default_player_state()
        scene = self.get_scene(scene_id)
        scene_type = scene["type"]
        raw_scene = scene["raw"]

        if scene_type == "dice_check":
            return self._resolve_dice_check(scene, raw_scene)

        if scene_type == "skill_check":
            return self._resolve_skill_check(scene, raw_scene, player_state)

        if scene_type == "combat":
            return self._resolve_combat(scene, raw_scene, player_state)

        if scene_type in {"item", "heal", "buff"}:
            return self._resolve_effect_scene(scene, raw_scene, player_state)
        
        if scene_type == "random_event":
            return self._resolve_random_event(scene, raw_scene, player_state)

        if scene_type in {"death", "ending"}:
            scene["game_over"] = True
            return scene

        scene["game_over"] = False
        return scene

    def _resolve_dice_check(
        self,
        scene: dict[str, Any],
        raw_scene: dict[str, Any],
    ) -> dict[str, Any]:
        config = raw_scene["dice_check"]

        result = roll_check(
            dice=config.get("dice", "d20"),
            success_threshold=config["success_threshold"],
            modifier=config.get("modifier", 0),
        )

        next_scene_id = (
            config["success_scene"] if result["success"] else config["fail_scene"]
        )

        scene["check_result"] = result
        scene["next_scene"] = next_scene_id
        scene["resolved"] = True
        scene["game_over"] = False

        return scene

    def _resolve_skill_check(
        self,
        scene: dict[str, Any],
        raw_scene: dict[str, Any],
        player_state: dict[str, Any],
    ) -> dict[str, Any]:
        config = raw_scene["skill_check"]
        skill = config["skill"]

        stat_modifier = player_state.get("stats", {}).get(skill, 0)
        base_modifier = config.get("modifier", 0)
        total_modifier = stat_modifier + base_modifier

        result = roll_check(
            dice=config.get("dice", "d20"),
            success_threshold=config["success_threshold"],
            modifier=total_modifier,
        )

        next_scene_id = (
            config["success_scene"] if result["success"] else config["fail_scene"]
        )

        scene["check_result"] = result
        scene["skill"] = skill
        scene["next_scene"] = next_scene_id
        scene["resolved"] = True
        scene["game_over"] = False

        return scene

    def _resolve_combat(
        self,
        scene: dict[str, Any],
        raw_scene: dict[str, Any],
        player_state: dict[str, Any],
    ) -> dict[str, Any]:
        enemy_data = raw_scene["enemy"]
        combat_data = raw_scene["combat"]

        player = Fighter(
            id="player",
            name="Player",
            hp=player_state["hp"],
            attack=player_state["stats"]["attack"],
            defense=player_state["stats"]["defense"],
        )

        enemy = Fighter(
            id=enemy_data["id"],
            name=self.translate(enemy_data["name_key"]),
            hp=enemy_data["hp"],
            attack=enemy_data["attack"],
            defense=enemy_data["defense"],
        )

        result = run_combat(player, enemy)

        player_state["hp"] = player.hp

        player_won = result.winner == player.name
        next_scene_id = combat_data["win_scene"] if player_won else combat_data["lose_scene"]

        scene["combat_result"] = {
            "winner": result.winner,
            "loser": result.loser,
            "rounds": [
                {
                    "round_number": r.round_number,
                    "attacker": r.attacker,
                    "defender": r.defender,
                    "roll": r.roll,
                    "modifier": r.modifier,
                    "total": r.total,
                    "damage": r.damage,
                    "defender_hp_after": r.defender_hp_after,
                }
                for r in result.rounds
            ],
        }

        scene["player_state"] = player_state
        scene["next_scene"] = next_scene_id
        scene["resolved"] = True
        scene["game_over"] = False

        return scene

    def _resolve_effect_scene(
        self,
        scene: dict[str, Any],
        raw_scene: dict[str, Any],
        player_state: dict[str, Any],
    ) -> dict[str, Any]:
        effects = raw_scene.get("effects", [])

        for effect in effects:
            self._apply_effect(effect, player_state)

        scene["player_state"] = player_state
        scene["effects_applied"] = effects
        scene["next_scene"] = raw_scene.get("next_scene")
        scene["resolved"] = True
        scene["game_over"] = False

        return scene

    def _apply_effect(
        self,
        effect: dict[str, Any],
        player_state: dict[str, Any],
    ) -> None:
        if "add_item" in effect:
            item = effect["add_item"]
            if item not in player_state["items"]:
                player_state["items"].append(item)

        if "heal" in effect:
            amount = effect["heal"]["amount"]
            player_state["hp"] = min(
                player_state["max_hp"],
                player_state["hp"] + amount,
            )

        if "increase_stat" in effect:
            stat = effect["increase_stat"]["stat"]
            amount = effect["increase_stat"]["amount"]
            player_state["stats"][stat] = player_state["stats"].get(stat, 0) + amount

        if "decrease_stat" in effect:
            stat = effect["decrease_stat"]["stat"]
            amount = effect["decrease_stat"]["amount"]
            player_state["stats"][stat] = player_state["stats"].get(stat, 0) - amount

    def is_game_over(self, scene_id: str) -> bool:
        scene = self.story["scenes"].get(scene_id)

        if not scene:
            raise KeyError(f"Scene not found: {scene_id}")

        return scene.get("type") in {"death", "ending"}

    def get_default_player_state(self) -> dict[str, Any]:
        return {
            "hp": 20,
            "max_hp": 20,
            "items": [],
            "stats": {
                "attack": 3,
                "defense": 2,
                "intelligence": 1,
                "luck": 1,
                "wisdom": 1,
            },
        }
    
    def _resolve_random_event(
        self,
        scene: dict[str, Any],
        raw_scene: dict[str, Any],
        player_state: dict[str, Any],
    ) -> dict[str, Any]:
        outcomes = raw_scene["random_event"]["outcomes"]

        selected_outcome = random.choices(
            population=outcomes,
            weights=[outcome.get("weight", 1) for outcome in outcomes],
            k=1,
        )[0]

        for effect in selected_outcome.get("effects", []):
            self._apply_effect(effect, player_state)

        scene["random_result"] = {
            "id": selected_outcome["id"],
            "weight": selected_outcome.get("weight", 1),
            "effects": selected_outcome.get("effects", []),
        }

        scene["player_state"] = player_state
        scene["next_scene"] = selected_outcome["next_scene"]
        scene["resolved"] = True
        scene["game_over"] = False

        return scene