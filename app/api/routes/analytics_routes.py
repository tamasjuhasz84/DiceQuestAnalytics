"""Analytics-related API routes."""

from typing import Any

from fastapi import APIRouter

from app.analytics.reports import (
    get_choice_distribution,
    get_combat_stats,
    get_death_reasons,
    get_dice_stats,
    get_language_stats,
    get_scene_popularity,
    get_session_funnel,
    get_summary_metrics,
    get_timeline_activity,
    load_events_df,
    load_sessions_df,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary() -> dict[str, Any]:
    """Return top-level summary metrics."""
    df = load_events_df()
    return get_summary_metrics(df)


@router.get("/choices")
async def analytics_choices() -> dict[str, Any]:
    """Return choice distribution data."""
    df = load_events_df()
    choices_df = get_choice_distribution(df)
    return {"items": choices_df.to_dict(orient="records")}


@router.get("/deaths")
async def analytics_deaths() -> dict[str, Any]:
    """Return death reason distribution."""
    df = load_events_df()
    death_df = get_death_reasons(df)
    return {"items": death_df.to_dict(orient="records")}


@router.get("/scenes")
async def analytics_scenes() -> dict[str, Any]:
    """Return scene popularity counts."""
    df = load_events_df()
    scene_df = get_scene_popularity(df)
    return {"items": scene_df.to_dict(orient="records")}


@router.get("/dice")
async def analytics_dice() -> dict[str, Any]:
    """Return dice roll metrics."""
    df = load_events_df()
    return get_dice_stats(df)


@router.get("/combat")
async def analytics_combat() -> dict[str, Any]:
    """Return combat aggregate metrics."""
    df = load_events_df()
    return get_combat_stats(df)


@router.get("/languages")
async def analytics_languages() -> dict[str, Any]:
    """Return session count per language."""
    sessions_df = load_sessions_df()
    lang_df = get_language_stats(sessions_df)
    return {"items": lang_df.to_dict(orient="records")}


@router.get("/funnel")
async def analytics_funnel() -> dict[str, Any]:
    """Return session funnel stage counts."""
    df = load_events_df()
    return {"items": get_session_funnel(df)}


@router.get("/timeline")
async def analytics_timeline() -> dict[str, Any]:
    """Return daily event activity counts."""
    df = load_events_df()
    return {"items": get_timeline_activity(df)}
