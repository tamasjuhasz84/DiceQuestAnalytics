"""Streamlit game page for DiceQuest Analytics."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
import streamlit as st

from api_client import ApiError, get_scene, resolve_scene, start_game, submit_choice
from i18n import (
    get_combat_column_map,
    get_current_language,
    render_language_selector,
    t,
    translate_item,
)

st.set_page_config(
    page_title="DiceQuest Analytics - Game",
    page_icon="D",
    layout="wide",
)


def _init_state() -> None:
    defaults = {
        "session_id": None,
        "player_state": {},
        "current_scene": {},
        "language": "hu",
        "awaiting_continue": False,
        "last_combat_animation_key": None,
        "session_end_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _arrow_safe_table(df: pd.DataFrame) -> pd.DataFrame:
    safe_df = df.copy()
    object_columns = safe_df.select_dtypes(include=["object"]).columns
    for column in object_columns:
        safe_df[column] = safe_df[column].astype(str)
    return safe_df


def _apply_scene_payload(payload: dict[str, Any], scene_key: str = "scene") -> None:
    st.session_state["current_scene"] = payload.get(scene_key, {})
    st.session_state["player_state"] = payload.get("player_state", {})


def _start_new_game() -> None:
    try:
        payload = start_game(get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    st.session_state["session_id"] = payload.get("session_id")
    st.session_state["current_scene"] = payload.get("start_scene", {})
    st.session_state["player_state"] = payload.get("player_state", {})
    st.session_state["awaiting_continue"] = False
    st.session_state["session_end_message"] = None
    st.session_state["last_combat_animation_key"] = None
    st.rerun()


def _refresh_scene() -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        return

    try:
        payload = get_scene(session_id, get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    _apply_scene_payload(payload)


def _on_choice(choice_id: str) -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        st.error(t("no_active_session"))
        return

    try:
        payload = submit_choice(session_id, choice_id, get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    _apply_scene_payload(payload)
    st.session_state["awaiting_continue"] = False
    st.session_state["last_combat_animation_key"] = None
    st.rerun()


def _on_roll_check() -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        st.error(t("no_active_session"))
        return

    try:
        payload = resolve_scene(session_id, get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    _apply_scene_payload(payload)
    st.session_state["awaiting_continue"] = True
    st.rerun()


def _on_fight() -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        st.error(t("no_active_session"))
        return

    try:
        payload = resolve_scene(session_id, get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    _apply_scene_payload(payload)
    st.session_state["awaiting_continue"] = True
    st.session_state["last_combat_animation_key"] = None
    st.rerun()


def _on_continue_after_resolve() -> None:
    _refresh_scene()
    st.session_state["awaiting_continue"] = False
    st.rerun()


def _on_continue_generic() -> None:
    session_id = st.session_state.get("session_id")
    if not session_id:
        st.error(t("no_active_session"))
        return

    try:
        payload = resolve_scene(session_id, get_current_language())
    except ApiError as exc:
        st.error(str(exc))
        return

    _apply_scene_payload(payload)
    _refresh_scene()
    st.session_state["awaiting_continue"] = False
    st.rerun()


def _end_quest() -> None:
    st.session_state["session_id"] = None
    st.session_state["current_scene"] = {}
    st.session_state["player_state"] = {}
    st.session_state["awaiting_continue"] = False
    st.session_state["last_combat_animation_key"] = None
    st.session_state["session_end_message"] = t("quest_ended")
    st.rerun()


def _get_scene_next_scene(scene: dict[str, Any]) -> str | None:
    next_scene = scene.get("next_scene")
    if isinstance(next_scene, str):
        return next_scene

    raw_next_scene = scene.get("raw", {}).get("next_scene")
    if isinstance(raw_next_scene, str):
        return raw_next_scene

    return None


def _render_check_result(scene: dict[str, Any]) -> None:
    check_result = scene.get("check_result")
    if not isinstance(check_result, dict):
        return

    dice_name = check_result.get("dice")
    if not dice_name and check_result.get("sides") is not None:
        dice_name = f"d{check_result.get('sides')}"

    roll_value = check_result.get("value", check_result.get("roll", "-"))
    modifier_value = check_result.get("modifier", 0)
    total_value = check_result.get("total")

    if total_value is None and isinstance(roll_value, (int, float)) and isinstance(modifier_value, (int, float)):
        total_value = roll_value + modifier_value

    target_value = check_result.get("success_threshold", "-")
    success_value = check_result.get("success")

    if success_value is None and isinstance(total_value, (int, float)) and isinstance(target_value, (int, float)):
        success_value = total_value >= target_value

    st.write(f"**{t('dice')}:** {dice_name or '-'}")
    st.write(f"**{t('target_value')}:** {target_value}")
    st.write(f"**{t('roll')}:** {roll_value}")
    st.write(f"**{t('modifier')}:** {modifier_value}")
    st.write(f"**{t('total')}:** {total_value if total_value is not None else '-'}")

    if success_value is True:
        st.success(f"{t('result')}: {t('success')}")
    elif success_value is False:
        st.error(f"{t('result')}: {t('failure')}")
    else:
        st.info(f"{t('result')}: -")

    st.caption(t("dice_explanation"))


def _translate_combat_rounds(rounds: list[dict[str, Any]]) -> pd.DataFrame:
    if not rounds:
        return pd.DataFrame()

    df = pd.DataFrame(rounds)
    mapping = get_combat_column_map()
    df = df.rename(columns=mapping)
    ordered_columns = [
        mapping[key]
        for key in [
            "round_number",
            "attacker",
            "defender",
            "roll",
            "modifier",
            "total",
            "damage",
            "defender_hp_after",
        ]
        if mapping.get(key) in df.columns
    ]

    if ordered_columns:
        df = df[ordered_columns]

    return df


def _render_rounds_progressive(df: pd.DataFrame, scene_id: str) -> None:
    if df.empty:
        return

    animation_key = f"{scene_id}:{len(df)}"
    if st.session_state.get("last_combat_animation_key") == animation_key:
        st.table(_arrow_safe_table(df))
        return

    placeholder = st.empty()
    for idx in range(len(df)):
        partial_df = df.iloc[: idx + 1]
        placeholder.table(_arrow_safe_table(partial_df))
        time.sleep(0.5)

    st.session_state["last_combat_animation_key"] = animation_key


def _render_player_state(player_state: dict[str, Any]) -> None:
    stats = player_state.get("stats", {})
    items = player_state.get("items", [])

    st.subheader(t("player"))
    st.caption(t("player_stats"))
    col1, col2 = st.columns(2)

    with col1:
        st.metric(t("hp"), f"{player_state.get('hp', 0)} / {player_state.get('max_hp', 0)}")
        st.metric(t("attack"), stats.get("attack", 0))
        st.metric(t("defense"), stats.get("defense", 0))

    with col2:
        st.metric(t("intelligence"), stats.get("intelligence", 0))
        st.metric(t("luck"), stats.get("luck", 0))
        st.metric(t("wisdom"), stats.get("wisdom", 0))

    translated_items = [translate_item(str(item)) for item in items]
    st.write(f"{t('items')}: {', '.join(translated_items) if translated_items else t('none')}")


def _render_enemy_preview(scene: dict[str, Any]) -> None:
    enemy = scene.get("enemy_preview")
    if not isinstance(enemy, dict):
        enemy = scene.get("raw", {}).get("enemy", {})

    if not isinstance(enemy, dict) or not enemy:
        return

    st.subheader(t("enemy"))
    st.write(f"**{t('enemy_name')}:** {enemy.get('name', '-')}")
    st.write(f"**{t('hp')}:** {enemy.get('hp', '-')}")
    st.write(f"**{t('attack')}:** {enemy.get('attack', '-')}")
    st.write(f"**{t('defense')}:** {enemy.get('defense', '-')}")


def _render_combat_result(scene: dict[str, Any], player_state: dict[str, Any]) -> None:
    combat_result = scene.get("combat_result")
    if not isinstance(combat_result, dict):
        return

    st.subheader(t("combat_result"))
    st.write(f"**{t('winner')}:** {combat_result.get('winner', '-')}")
    st.write(f"**{t('loser')}:** {combat_result.get('loser', '-')}")
    st.write(f"**{t('player_hp_after')}:** {player_state.get('hp', '-')}")

    rounds = combat_result.get("rounds", [])
    if isinstance(rounds, list) and rounds:
        translated_rounds = _translate_combat_rounds(rounds)
        _render_rounds_progressive(translated_rounds, str(scene.get("id", "combat")))

    if combat_result.get("winner") == "Player":
        st.success(t("attack_reward"))


_init_state()
language_changed = render_language_selector()

if language_changed:
    st.session_state["last_combat_animation_key"] = None
    if st.session_state.get("session_id"):
        _refresh_scene()
    st.rerun()

st.title(t("game_page_title"))

if not st.session_state.get("session_id"):
    if st.session_state.get("session_end_message"):
        st.success(str(st.session_state["session_end_message"]))

    st.warning(t("no_active_session"))
    if st.button(t("start_new_game"), type="primary"):
        _start_new_game()
    st.stop()

if not st.session_state.get("current_scene"):
    _refresh_scene()

current_scene = st.session_state.get("current_scene", {})
player_state = st.session_state.get("player_state", {})
scene_type = current_scene.get("type")
is_check_scene = scene_type in {"dice_check", "skill_check"}
is_combat_scene = scene_type == "combat"

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader(current_scene.get("title", t("unknown_scene")))
    st.write(current_scene.get("text", t("no_scene_text")))

    if current_scene.get("game_over"):
        st.error(t("game_over"))
        if st.button(t("start_new_game"), key="game_over_start", type="primary"):
            _start_new_game()
        st.stop()

    if is_check_scene and not isinstance(current_scene.get("check_result"), dict):
        if st.button(t("roll_dice"), type="primary", key="roll_dice"):
            _on_roll_check()
    elif is_check_scene and isinstance(current_scene.get("check_result"), dict):
        _render_check_result(current_scene)
        if st.button(t("continue"), type="primary", key="check_continue"):
            _on_continue_after_resolve()

    elif is_combat_scene and not isinstance(current_scene.get("combat_result"), dict):
        _render_enemy_preview(current_scene)
        combat_col1, combat_col2 = st.columns(2)
        with combat_col1:
            if st.button(t("fight"), type="primary", key="fight"):
                _on_fight()
        with combat_col2:
            if st.button(t("end_quest"), key="end_quest"):
                _end_quest()

    elif is_combat_scene and isinstance(current_scene.get("combat_result"), dict):
        _render_enemy_preview(current_scene)
        _render_combat_result(current_scene, player_state)
        if st.button(t("continue"), type="primary", key="combat_continue"):
            _on_continue_after_resolve()

    else:
        choices = [
            choice
            for choice in current_scene.get("choices", [])
            if isinstance(choice, dict) and choice.get("id")
        ]
        next_scene_id = _get_scene_next_scene(current_scene)

        if len(choices) == 1:
            if st.button(t("continue"), type="primary", key="single_choice_continue"):
                _on_choice(str(choices[0]["id"]))
        elif len(choices) > 1:
            st.subheader(t("choices"))
            for choice in choices:
                choice_id = str(choice.get("id", ""))
                choice_label = str(choice.get("label", choice_id))
                if st.button(choice_label, key=f"choice_{choice_id}"):
                    _on_choice(choice_id)
        elif next_scene_id:
            if st.button(t("continue"), type="primary", key="generic_continue"):
                _on_continue_generic()
        else:
            if st.button(t("continue"), type="primary", key="fallback_continue"):
                _on_continue_generic()

with col2:
    _render_player_state(player_state)
