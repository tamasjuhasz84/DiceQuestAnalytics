"""Streamlit analytics page for DiceQuest Analytics."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from api_client import ApiError, get_analytics_combat, get_analytics_deaths, get_analytics_summary
from i18n import render_language_selector, t

st.set_page_config(
    page_title="DiceQuest Analytics - Analytics",
    page_icon="A",
    layout="wide",
)


def _arrow_safe_table(df: pd.DataFrame) -> pd.DataFrame:
    safe_df = df.copy()
    object_columns = safe_df.select_dtypes(include=["object"]).columns
    for column in object_columns:
        safe_df[column] = safe_df[column].astype(str)
    return safe_df


def _fetch_data() -> tuple[dict, list[dict], dict]:
    try:
        summary = get_analytics_summary()
        deaths = get_analytics_deaths().get("deaths", [])
        combat = get_analytics_combat()
        return summary, deaths, combat
    except ApiError as exc:
        st.error(str(exc))
        return {}, [], {}


language_changed = render_language_selector()
if language_changed:
    st.rerun()

st.title(t("analytics_page_title"))
summary, deaths, combat = _fetch_data()

st.subheader(t("summary"))
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(t("total_sessions"), summary.get("total_sessions", 0))
with col2:
    st.metric(t("completed_sessions"), summary.get("completed_sessions", 0))
with col3:
    avg_choices = summary.get("average_choices_per_session", 0)
    st.metric(t("avg_choices"), f"{avg_choices:.2f}")

st.subheader(t("deaths"))
if deaths:
    deaths_df = _arrow_safe_table(pd.DataFrame(deaths))
    if "reason" in deaths_df.columns and "count" in deaths_df.columns:
        deaths_df["reason"] = deaths_df["reason"].astype(str)
        deaths_df["count"] = pd.to_numeric(deaths_df["count"], errors="coerce").fillna(0)
        st.bar_chart(deaths_df.set_index("reason")["count"])
    st.dataframe(deaths_df, use_container_width=True)
else:
    st.info(t("no_death_data"))

st.subheader(t("combat"))
if combat:
    combat_stats = {
        t("total_combats"): combat.get("total_combats", 0),
        t("player_wins"): combat.get("player_wins", 0),
        t("avg_combat_rounds"): float(combat.get("average_rounds", 0) or 0),
    }
    st.dataframe(pd.DataFrame([combat_stats]), use_container_width=True)
else:
    st.info(t("no_combat_data"))
