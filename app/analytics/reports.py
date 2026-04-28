"""Pandas-based analytics reports built from SQLite event logs."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.models.database import get_connection


def _safe_load_json(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value:
        return {}

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return {}

    if isinstance(payload, dict):
        return payload

    return {}


def load_events_df() -> pd.DataFrame:
    """Load events into DataFrame with parsed JSON and datetime fields."""
    query = "SELECT id, session_id, event_type, scene_id, data_json, created_at FROM events"

    with get_connection() as connection:
        df = pd.read_sql_query(query, connection)

    if df.empty:
        return df

    df["data"] = df["data_json"].apply(_safe_load_json)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    return df


def get_summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Build high-level summary metrics for dashboard cards."""
    if df.empty:
        return {
            "total_games": 0,
            "total_events": 0,
            "total_deaths": 0,
            "total_wins": 0,
            "win_rate": 0.0,
        }

    total_games = int(df["session_id"].nunique())
    total_events = int(len(df))
    total_deaths = int((df["event_type"] == "death").sum())
    total_wins = int((df["event_type"] == "ending").sum())
    win_rate = float(total_wins / total_games) if total_games else 0.0

    return {
        "total_games": total_games,
        "total_events": total_events,
        "total_deaths": total_deaths,
        "total_wins": total_wins,
        "win_rate": win_rate,
    }


def get_choice_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Return how many times each choice_id was selected."""
    if df.empty:
        return pd.DataFrame(columns=["choice_id", "count"])

    choices = df[df["event_type"] == "choice"].copy()
    if choices.empty:
        return pd.DataFrame(columns=["choice_id", "count"])

    choices["choice_id"] = choices["data"].apply(lambda data: data.get("choice_id"))
    result = (
        choices.dropna(subset=["choice_id"])
        .groupby("choice_id", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return result


def get_death_reasons(df: pd.DataFrame) -> pd.DataFrame:
    """Return count of death reasons from event data_json."""
    if df.empty:
        return pd.DataFrame(columns=["death_reason", "count"])

    deaths = df[df["event_type"] == "death"].copy()
    if deaths.empty:
        return pd.DataFrame(columns=["death_reason", "count"])

    deaths["death_reason"] = deaths.apply(
        lambda row: row["data"].get("death_reason")
        or row["data"].get("reason")
        or row.get("scene_id")
        or "unknown",
        axis=1,
    )

    result = (
        deaths.groupby("death_reason", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return result


def get_scene_popularity(df: pd.DataFrame) -> pd.DataFrame:
    """Return most frequently visited scene ids."""
    if df.empty:
        return pd.DataFrame(columns=["scene_id", "count"])

    result = (
        df.dropna(subset=["scene_id"])
        .groupby("scene_id", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return result


def get_dice_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Return average dice roll and roll distribution for check events."""
    if df.empty:
        return {"average_roll": 0.0, "distribution": []}

    checks = df[df["event_type"].isin(["dice_check", "skill_check"])].copy()
    if checks.empty:
        return {"average_roll": 0.0, "distribution": []}

    checks["roll"] = checks["data"].apply(
        lambda data: (data.get("check_result") or {}).get("roll")
    )
    checks = checks.dropna(subset=["roll"])

    if checks.empty:
        return {"average_roll": 0.0, "distribution": []}

    checks["roll"] = pd.to_numeric(checks["roll"], errors="coerce")
    checks = checks.dropna(subset=["roll"])
    if checks.empty:
        return {"average_roll": 0.0, "distribution": []}

    distribution_df = (
        checks.groupby("roll", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("roll")
    )
    distribution_df["roll"] = distribution_df["roll"].astype(int)

    return {
        "average_roll": float(checks["roll"].mean()),
        "distribution": distribution_df.to_dict(orient="records"),
    }


def get_combat_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Return combat totals, win rate and average rounds."""
    if df.empty:
        return {"total_combats": 0, "win_rate": 0.0, "average_rounds": 0.0}

    combats = df[df["event_type"] == "combat"].copy()
    if combats.empty:
        return {"total_combats": 0, "win_rate": 0.0, "average_rounds": 0.0}

    combats["winner"] = combats["data"].apply(
        lambda data: (data.get("combat_result") or {}).get("winner")
    )
    combats["round_count"] = combats["data"].apply(
        lambda data: len((data.get("combat_result") or {}).get("rounds", []))
    )

    total_combats = int(len(combats))
    won_combats = int((combats["winner"] == "Player").sum())
    win_rate = float(won_combats / total_combats) if total_combats else 0.0
    average_rounds = float(combats["round_count"].mean()) if total_combats else 0.0

    return {
        "total_combats": total_combats,
        "win_rate": win_rate,
        "average_rounds": average_rounds,
    }
