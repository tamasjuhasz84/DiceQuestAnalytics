"""Shared i18n helpers for Streamlit pages."""

from __future__ import annotations

import streamlit as st
from ui_translations import COMBAT_COLUMN_TRANSLATIONS, ITEM_TRANSLATIONS, UI_TRANSLATIONS


def get_current_language() -> str:
    """Return current language from session state, defaulting to Hungarian."""
    language = st.session_state.get("language", "hu")
    if language not in UI_TRANSLATIONS:
        return "hu"
    return language


def t(key: str, lang: str | None = None) -> str:
    """Translate UI key with fallback: selected lang -> hu -> key."""
    selected = lang or get_current_language()
    return (
        UI_TRANSLATIONS.get(selected, {}).get(key) or UI_TRANSLATIONS.get("hu", {}).get(key) or key
    )


def translate_item(item_id: str, lang: str | None = None) -> str:
    """Translate item id to display name."""
    selected = lang or get_current_language()
    return ITEM_TRANSLATIONS.get(item_id, {}).get(selected, item_id)


def get_combat_column_map(lang: str | None = None) -> dict[str, str]:
    """Return translated combat table column mapping."""
    selected = lang or get_current_language()
    return COMBAT_COLUMN_TRANSLATIONS.get(selected, COMBAT_COLUMN_TRANSLATIONS["en"])


def get_language_options() -> dict[str, str]:
    """Return UI language selector options."""
    return {"Magyar": "hu", "English": "en"}


def render_language_selector() -> bool:
    """Render sidebar selector, store language, return whether it changed."""
    previous_language = get_current_language()
    options = get_language_options()

    current_label = "Magyar" if previous_language == "hu" else "English"
    selected_label = st.sidebar.selectbox(
        t("language", previous_language),
        options=list(options.keys()),
        index=list(options.keys()).index(current_label),
    )

    selected_language = options[selected_label]
    st.session_state["language"] = selected_language
    return selected_language != previous_language
