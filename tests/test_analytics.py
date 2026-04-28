"""Tests for analytics report helpers."""

import pandas as pd

from app.analytics.reports import (
    get_choice_distribution,
    get_combat_stats,
    get_death_reasons,
    get_dice_stats,
    get_scene_popularity,
    get_summary_metrics,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "session_id": "s1",
                "event_type": "game_started",
                "scene_id": "intro_01",
                "data": {},
            },
            {
                "session_id": "s1",
                "event_type": "choice",
                "scene_id": "intro_01",
                "data": {"choice_id": "enter_gate", "resulting_scene_id": "intro_02"},
            },
            {
                "session_id": "s1",
                "event_type": "dice_check",
                "scene_id": "intro_03",
                "data": {"check_result": {"roll": 12}},
            },
            {
                "session_id": "s2",
                "event_type": "combat",
                "scene_id": "str_02",
                "data": {"combat_result": {"winner": "Player", "rounds": [{}, {}]}},
            },
            {
                "session_id": "s2",
                "event_type": "death",
                "scene_id": "death_trap_01",
                "data": {"death_reason": "trap"},
            },
            {
                "session_id": "s2",
                "event_type": "ending",
                "scene_id": "final_01",
                "data": {},
            },
        ]
    )


def test_summary_metrics() -> None:
    """Summary metrics should include key totals and win rate."""
    metrics = get_summary_metrics(_sample_df())
    assert metrics["total_games"] == 2
    assert metrics["total_events"] == 6
    assert metrics["total_deaths"] == 1
    assert metrics["total_wins"] == 1
    assert metrics["win_rate"] == 0.5


def test_choice_distribution() -> None:
    """Choice distribution should count choice ids."""
    result = get_choice_distribution(_sample_df())
    assert not result.empty
    assert "choice_id" in result.columns
    assert "count" in result.columns
    assert int(result.iloc[0]["count"]) >= 1


def test_death_reasons() -> None:
    """Death reasons should be extracted from data."""
    result = get_death_reasons(_sample_df())
    assert not result.empty
    assert "death_reason" in result.columns
    assert "count" in result.columns


def test_scene_popularity() -> None:
    """Scene popularity should aggregate scene occurrences."""
    result = get_scene_popularity(_sample_df())
    assert not result.empty
    assert "scene_id" in result.columns
    assert "count" in result.columns


def test_dice_and_combat_stats() -> None:
    """Dice and combat helpers should return expected keys."""
    df = _sample_df()
    dice = get_dice_stats(df)
    combat = get_combat_stats(df)

    assert "average_roll" in dice
    assert "distribution" in dice
    assert combat["total_combats"] == 1
    assert combat["average_rounds"] == 2.0


def test_helpers_return_empty_structures_for_empty_df() -> None:
    empty_df = pd.DataFrame()

    summary = get_summary_metrics(empty_df)
    choices = get_choice_distribution(empty_df)
    deaths = get_death_reasons(empty_df)
    scenes = get_scene_popularity(empty_df)
    dice = get_dice_stats(empty_df)
    combat = get_combat_stats(empty_df)

    assert summary["total_games"] == 0
    assert choices.empty
    assert deaths.empty
    assert scenes.empty
    assert dice["distribution"] == []
    assert combat["total_combats"] == 0
