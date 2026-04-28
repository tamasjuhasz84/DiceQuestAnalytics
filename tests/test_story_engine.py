"""Unit tests for StoryEngine behavior."""

from app.core.combat import CombatResult, CombatRound
from app.core.story_engine import StoryEngine


def _engine_hu() -> StoryEngine:
    return StoryEngine(story_path="data/story.yaml", locale_path="data/i18n/hu.yaml")


def test_get_start_scene_and_scene_data() -> None:
    engine = _engine_hu()

    start_scene_id = engine.get_start_scene_id()
    scene = engine.get_scene(start_scene_id)

    assert start_scene_id == "intro_01"
    assert scene["id"] == "intro_01"
    assert isinstance(scene["title"], str)
    assert isinstance(scene["text"], str)
    assert isinstance(scene["choices"], list)


def test_choose_invalid_raises_value_error() -> None:
    engine = _engine_hu()

    try:
        engine.choose("intro_01", "invalid_choice")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid choice")


def test_resolve_item_scene_applies_effects() -> None:
    engine = _engine_hu()
    player_state = engine.get_default_player_state()

    resolved = engine.resolve_scene("str_01", player_state)

    assert resolved["resolved"] is True
    assert resolved["next_scene"] == "str_02"
    assert "sword" in resolved["player_state"]["items"]
    assert resolved["player_state"]["stats"]["attack"] >= 5


def test_resolve_dice_check_uses_roll_check_result(monkeypatch) -> None:
    engine = _engine_hu()

    monkeypatch.setattr(
        "app.core.story_engine.roll_check",
        lambda **_kwargs: {
            "dice": "d20",
            "sides": 20,
            "value": 18,
            "modifier": 0,
            "total": 18,
            "success_threshold": 11,
            "success": True,
            "is_critical_success": False,
            "is_critical_failure": False,
        },
    )

    resolved = engine.resolve_scene("intro_03", engine.get_default_player_state())

    assert resolved["resolved"] is True
    assert resolved["check_result"]["success"] is True
    assert resolved["next_scene"] == "luck_01"


def test_resolve_combat_uses_combat_result(monkeypatch) -> None:
    engine = _engine_hu()

    fake_round = CombatRound(
        round_number=1,
        attacker="Player",
        defender="Goblin",
        roll=5,
        modifier=4,
        total=9,
        damage=8,
        defender_hp_after=0,
    )
    fake_result = CombatResult(winner="Player", loser="Goblin", rounds=[fake_round])

    monkeypatch.setattr("app.core.story_engine.run_combat", lambda _p, _e: fake_result)

    player_state = engine.get_default_player_state()
    resolved = engine.resolve_scene("str_02", player_state)

    assert resolved["resolved"] is True
    assert resolved["combat_result"]["winner"] == "Player"
    assert resolved["next_scene"] == "str_03"


def test_resolve_random_event_applies_selected_effect(monkeypatch) -> None:
    engine = _engine_hu()
    player_state = engine.get_default_player_state()

    monkeypatch.setattr(
        "app.core.story_engine.random.choices",
        lambda population, **_kwargs: [population[0]],
    )

    resolved = engine.resolve_scene("luck_02", player_state)

    assert resolved["resolved"] is True
    assert resolved["random_result"]["id"] == "gold_reward"
    assert "golden_token" in resolved["player_state"]["items"]
    assert resolved["next_scene"] == "luck_03"
