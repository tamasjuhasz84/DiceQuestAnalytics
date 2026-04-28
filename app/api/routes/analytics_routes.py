"""Analytics-related API routes."""

from typing import Any

from fastapi import APIRouter

from app.analytics.reports import (
    get_choice_distribution,
    get_combat_stats,
    get_death_reasons,
    get_dice_stats,
    get_scene_popularity,
    get_summary_metrics,
    load_events_df,
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
