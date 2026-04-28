"""Pandas-based analytics reports built from SQLite event logs."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from app.models.database import get_connection, init_db

_DEATH_EVENT_TYPES = {"death", "player_death"}
_COMBAT_EVENT_TYPES = {"combat", "combat_started", "combat_finished"}
_DICE_EVENT_TYPES = {"dice_check", "skill_check", "dice_roll"}


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
    init_db()
    query = "SELECT id, session_id, event_type, scene_id, data_json, created_at FROM events"
    try:
        with get_connection() as connection:
            df = pd.read_sql_query(query, connection)
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    df["data"] = df["data_json"].apply(_safe_load_json)
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    return df


def load_sessions_df() -> pd.DataFrame:
    """Load sessions into DataFrame."""
    init_db()
    query = "SELECT id, language, created_at FROM sessions"
    try:
        with get_connection() as connection:
            df = pd.read_sql_query(query, connection)
    except Exception:
        return pd.DataFrame(columns=["id", "language", "created_at"])

    if not df.empty:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    return df


def get_summary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Build high-level summary metrics for dashboard cards."""
    if df.empty:
        return {
            "total_games": 0,
            "total_sessions": 0,
            "total_events": 0,
            "total_deaths": 0,
            "total_wins": 0,
            "completed_sessions": 0,
            "average_choices_per_session": 0.0,
            "win_rate": 0.0,
        }

    total_games = int(df["session_id"].nunique())
    total_events = int(len(df))
    total_deaths = int(df["event_type"].isin(_DEATH_EVENT_TYPES).sum())
    total_wins = int((df["event_type"] == "ending").sum())
    total_choices = int((df["event_type"] == "choice").sum())
    average_choices_per_session = float(total_choices / total_games) if total_games else 0.0
    win_rate = float(total_wins / total_games) if total_games else 0.0

    return {
        "total_games": total_games,
        "total_sessions": total_games,
        "total_events": total_events,
        "total_deaths": total_deaths,
        "total_wins": total_wins,
        "completed_sessions": total_wins,
        "average_choices_per_session": average_choices_per_session,
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

    deaths = df[df["event_type"].isin(_DEATH_EVENT_TYPES)].copy()
    if deaths.empty:
        return pd.DataFrame(columns=["death_reason", "count"])

    deaths["death_reason"] = deaths.apply(
        lambda row: (
            row["data"].get("death_reason")
            or row["data"].get("reason")
            or row.get("scene_id")
            or "unknown"
        ),
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

    checks = df[df["event_type"].isin(_DICE_EVENT_TYPES)].copy()
    if checks.empty:
        return {"average_roll": 0.0, "distribution": []}

    # `roll_check` stores the face value under `value`; keep `roll` as fallback for compatibility.
    checks["roll"] = checks["data"].apply(
        lambda data: (data.get("check_result") or {}).get("value")
        if isinstance(data, dict)
        else None
    )
    checks.loc[checks["roll"].isna(), "roll"] = checks["data"].apply(
        lambda data: (data.get("check_result") or {}).get("roll")
        if isinstance(data, dict)
        else None
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
        return {"total_combats": 0, "player_wins": 0, "win_rate": 0.0, "average_rounds": 0.0}

    combats = df[
        (df["event_type"].isin(_COMBAT_EVENT_TYPES))
        | (df["data"].apply(lambda data: isinstance(data, dict) and data.get("combat_result") is not None))
    ].copy()
    if combats.empty:
        return {"total_combats": 0, "player_wins": 0, "win_rate": 0.0, "average_rounds": 0.0}

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
        "player_wins": won_combats,
        "win_rate": win_rate,
        "average_rounds": average_rounds,
    }


def get_language_stats(sessions_df: pd.DataFrame) -> pd.DataFrame:
    """Return session count per language."""
    if sessions_df.empty or "language" not in sessions_df.columns:
        return pd.DataFrame(columns=["language", "count"])

    result = (
        sessions_df.groupby("language", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("count", ascending=False)
    )
    return result


_FUNNEL_STAGES = [
    ("started", {"game_started"}),
    ("made_choice", {"choice"}),
    ("encountered_challenge", {"combat", "dice_check", "skill_check"}),
    ("finished", {"death", "ending"}),
]


def get_session_funnel(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return session counts per funnel stage."""
    if df.empty:
        return [{"stage": stage, "count": 0} for stage, _ in _FUNNEL_STAGES]

    result = []
    for stage, event_types in _FUNNEL_STAGES:
        count = int(df[df["event_type"].isin(event_types)]["session_id"].nunique())
        result.append({"stage": stage, "count": count})
    return result


def get_timeline_activity(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Return daily event counts for an activity timeline."""
    if df.empty or "created_at" not in df.columns:
        return []

    timed = df.dropna(subset=["created_at"]).copy()
    if timed.empty:
        return []

    timed["date"] = timed["created_at"].dt.date.astype(str)
    result = (
        timed.groupby("date", as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values("date")
    )
    return result.to_dict(orient="records")
