"""Streamlit analytics dashboard for DiceQuest Analytics."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from api_client import (
    ApiError,
    get_analytics_choices,
    get_analytics_combat,
    get_analytics_deaths,
    get_analytics_dice,
    get_analytics_funnel,
    get_analytics_languages,
    get_analytics_scenes,
    get_analytics_summary,
    get_analytics_timeline,
)
from i18n import render_language_selector, t

st.set_page_config(
    page_title="DiceQuest Analytics - Analytics",
    page_icon="📊",
    layout="wide",
)


def _arrow_safe_table(df: pd.DataFrame) -> pd.DataFrame:
    safe_df = df.copy()
    for col in safe_df.select_dtypes(include=["object"]).columns:
        safe_df[col] = safe_df[col].astype(str)
    return safe_df


def _fetch_all() -> dict:
    """Fetch all analytics data from the backend, returning safe defaults on error."""
    empty: dict = {
        "summary": {},
        "deaths": [],
        "combat": {},
        "choices": [],
        "scenes": [],
        "dice": {},
        "languages": [],
        "funnel": [],
        "timeline": [],
    }
    try:
        empty["summary"] = get_analytics_summary()
        empty["deaths"] = get_analytics_deaths().get("items", [])
        empty["combat"] = get_analytics_combat()
        empty["choices"] = get_analytics_choices().get("items", [])
        empty["scenes"] = get_analytics_scenes().get("items", [])
        empty["dice"] = get_analytics_dice()
        empty["languages"] = get_analytics_languages().get("items", [])
        empty["funnel"] = get_analytics_funnel().get("items", [])
        empty["timeline"] = get_analytics_timeline().get("items", [])
    except ApiError as exc:
        st.error(str(exc))
    return empty


language_changed = render_language_selector()
if language_changed:
    st.rerun()

st.title(t("analytics_page_title"))
st.caption(t("analytics_subtitle"))

data = _fetch_all()
summary = data["summary"]
deaths = data["deaths"]
combat = data["combat"]
choices = data["choices"]
scenes = data["scenes"]
dice = data["dice"]
languages = data["languages"]
funnel = data["funnel"]
timeline = data["timeline"]

# ── KPI row 1 ─────────────────────────────────────────────────────────────────
st.subheader(t("summary"))
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric(t("total_sessions"), summary.get("total_sessions", 0))
kpi2.metric(t("completed_sessions"), summary.get("completed_sessions", 0))
kpi3.metric(t("total_deaths"), summary.get("total_deaths", 0))

# ── KPI row 2 ─────────────────────────────────────────────────────────────────
kpi4, kpi5, kpi6 = st.columns(3)
avg_c = float(summary.get("average_choices_per_session", 0) or 0)
kpi4.metric(t("avg_choices"), f"{avg_c:.2f}")
avg_r = float(dice.get("average_roll", 0) or 0)
kpi5.metric(t("avg_roll"), f"{avg_r:.2f}" if avg_r else "—")
wr = float(combat.get("win_rate", 0) or 0)
kpi6.metric(t("combat_win_rate"), f"{wr * 100:.1f} %" if combat.get("total_combats") else "—")

st.divider()

# ── Choices ───────────────────────────────────────────────────────────────────
st.subheader(t("choices"))
if choices:
    ch_df = _arrow_safe_table(pd.DataFrame(choices))
    ch_df["count"] = pd.to_numeric(ch_df["count"], errors="coerce").fillna(0)
    st.bar_chart(ch_df.set_index("choice_id")["count"])
    st.dataframe(ch_df, use_container_width=True)
else:
    st.info(t("no_choices"))

st.divider()

# ── Scenes ────────────────────────────────────────────────────────────────────
st.subheader(t("scenes"))
if scenes:
    sc_df = _arrow_safe_table(pd.DataFrame(scenes))
    sc_df["count"] = pd.to_numeric(sc_df["count"], errors="coerce").fillna(0)
    st.bar_chart(sc_df.set_index("scene_id")["count"])
    st.dataframe(sc_df, use_container_width=True)
else:
    st.info(t("no_scenes"))

st.divider()

# ── Dice ──────────────────────────────────────────────────────────────────────
st.subheader(t("dice"))
distribution = dice.get("distribution", [])
if distribution:
    dist_df = _arrow_safe_table(pd.DataFrame(distribution))
    dist_df["roll"] = pd.to_numeric(dist_df["roll"], errors="coerce")
    dist_df["count"] = pd.to_numeric(dist_df["count"], errors="coerce").fillna(0)
    dist_df = dist_df.dropna(subset=["roll"]).copy()
    dist_df["roll"] = dist_df["roll"].astype(int)
    st.bar_chart(dist_df.set_index("roll")["count"])
    st.dataframe(dist_df, use_container_width=True)
else:
    st.info(t("no_dice"))

st.divider()

# ── Combat ────────────────────────────────────────────────────────────────────
st.subheader(t("combat"))
if combat and combat.get("total_combats", 0) > 0:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("total_combats"), combat["total_combats"])
    c2.metric(t("player_wins"), combat.get("player_wins", 0))
    c3.metric(t("combat_win_rate"), f"{float(combat.get('win_rate', 0)) * 100:.1f} %")
    c4.metric(t("avg_combat_rounds"), f"{float(combat.get('average_rounds', 0)):.1f}")
    combat_chart = pd.DataFrame(
        [
            {"category": t("total_combats"), "count": combat["total_combats"]},
            {"category": t("player_wins"), "count": combat.get("player_wins", 0)},
        ]
    )
    st.bar_chart(combat_chart.set_index("category")["count"])
else:
    st.info(t("no_combat_data"))

st.divider()

# ── Deaths ────────────────────────────────────────────────────────────────────
st.subheader(t("deaths"))
if deaths:
    d_df = _arrow_safe_table(pd.DataFrame(deaths))
    d_df["count"] = pd.to_numeric(d_df["count"], errors="coerce").fillna(0)
    st.bar_chart(d_df.set_index("death_reason")["count"])
    st.dataframe(d_df, use_container_width=True)
else:
    st.info(t("no_death_data"))

st.divider()

# ── Language usage ────────────────────────────────────────────────────────────
st.subheader(t("languages"))
if languages:
    lg_df = _arrow_safe_table(pd.DataFrame(languages))
    lg_df["count"] = pd.to_numeric(lg_df["count"], errors="coerce").fillna(0)
    st.bar_chart(lg_df.set_index("language")["count"])
    st.dataframe(lg_df, use_container_width=True)
else:
    st.info(t("no_language_data"))

st.divider()

# ── Activity timeline ─────────────────────────────────────────────────────────
st.subheader(t("timeline"))
if timeline:
    tl_df = _arrow_safe_table(pd.DataFrame(timeline))
    tl_df["count"] = pd.to_numeric(tl_df["count"], errors="coerce").fillna(0)
    st.line_chart(tl_df.set_index("date")["count"])
else:
    st.info(t("no_timeline_data"))

st.divider()

# ── Session funnel ────────────────────────────────────────────────────────────
st.subheader(t("session_funnel"))
if funnel:
    fn_df = _arrow_safe_table(pd.DataFrame(funnel))
    fn_df["count"] = pd.to_numeric(fn_df["count"], errors="coerce").fillna(0)
    st.bar_chart(fn_df.set_index("stage")["count"])
    st.dataframe(fn_df, use_container_width=True)
else:
    st.info(t("no_funnel_data"))
