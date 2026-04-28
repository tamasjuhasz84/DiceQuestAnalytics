"""Game-related API routes."""

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.event_logger import create_session_log, log_event
from app.core.story_engine import StoryEngine
from app.models.schemas import (
    ChoiceRequest,
    SceneResponse,
    StartGameResponse,
)

router = APIRouter(prefix="/game", tags=["game"])
SUPPORTED_LANGUAGES = {"hu", "en"}
story_engines = {
    "hu": StoryEngine(locale_path="data/i18n/hu.yaml"),
    "en": StoryEngine(locale_path="data/i18n/en.yaml"),
}

# In-memory session storage for MVP.
sessions: dict[str, dict[str, Any]] = {}

RESOLVE_EVENT_TYPES = {
    "dice_check",
    "skill_check",
    "combat",
    "random_event",
    "item",
    "heal",
    "buff",
    "death",
    "ending",
}


def _get_session_or_404(session_id: str) -> dict[str, Any]:
    session = sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _normalize_language(language: str | None) -> str:
    if isinstance(language, str) and language in SUPPORTED_LANGUAGES:
        return language
    return "hu"


def _engine_for_language(language: str) -> StoryEngine:
    return story_engines.get(language, story_engines["hu"])


def _resolve_scene_with_state(
    engine: StoryEngine,
    scene_id: str,
    player_state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved_scene = engine.resolve_scene(scene_id, player_state)
    updated_state = resolved_scene.get("player_state", player_state)
    return resolved_scene, updated_state


def _preview_scene(engine: StoryEngine, scene_id: str) -> dict[str, Any]:
    scene = engine.get_scene(scene_id)
    scene_type = str(scene.get("type", ""))
    scene["game_over"] = scene_type in {"death", "ending"}

    if scene_type == "combat":
        enemy_data = scene.get("raw", {}).get("enemy", {})
        scene["enemy_preview"] = {
            "name": engine.translate(enemy_data.get("name_key", "")),
            "hp": enemy_data.get("hp"),
            "attack": enemy_data.get("attack"),
            "defense": enemy_data.get("defense"),
        }

    return scene


def _build_resolve_log_data(
    scene: dict[str, Any],
    player_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "check_result": scene.get("check_result"),
        "combat_result": scene.get("combat_result"),
        "random_result": scene.get("random_result"),
        "effects_applied": scene.get("effects_applied"),
        "player_state": player_state,
        "next_scene": scene.get("next_scene"),
    }


@router.post("/start", response_model=StartGameResponse)
async def start_game(language: str = "hu") -> StartGameResponse:
    """Create a new session and return the start scene preview."""
    selected_language = _normalize_language(language)
    engine = _engine_for_language(selected_language)

    session_id = str(uuid4())
    current_scene = engine.get_start_scene_id()
    player_state = engine.get_default_player_state()

    start_scene = _preview_scene(engine, current_scene)

    sessions[session_id] = {
        "current_scene": current_scene,
        "player_state": player_state,
        "language": selected_language,
    }

    create_session_log(session_id=session_id, language=selected_language)
    log_event(
        session_id=session_id,
        event_type="game_started",
        scene_id=current_scene,
        data={
            "start_scene_id": start_scene.get("id"),
            "player_state": player_state,
        },
    )

    return StartGameResponse(
        session_id=session_id,
        start_scene=start_scene,
        player_state=player_state,
    )


@router.get("/{session_id}/scene", response_model=SceneResponse)
async def get_current_scene(session_id: str, language: str | None = None) -> SceneResponse:
    """Return the current scene preview for a session."""
    session = _get_session_or_404(session_id)
    if language is not None:
        session["language"] = _normalize_language(language)

    selected_language = _normalize_language(session.get("language"))
    engine = _engine_for_language(selected_language)
    scene = _preview_scene(engine, session["current_scene"])
    return SceneResponse(scene=scene, player_state=session["player_state"])


@router.post("/{session_id}/choice", response_model=SceneResponse)
async def make_choice(
    session_id: str,
    payload: ChoiceRequest,
    language: str | None = None,
) -> SceneResponse:
    """Apply a choice and move to the selected next scene preview."""
    session = _get_session_or_404(session_id)
    if language is not None:
        session["language"] = _normalize_language(language)

    selected_language = _normalize_language(session.get("language"))
    engine = _engine_for_language(selected_language)
    source_scene_id = str(session["current_scene"])

    try:
        next_scene = engine.choose(session["current_scene"], payload.choice_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    next_scene_id = str(next_scene["id"])
    session["current_scene"] = next_scene_id
    scene = _preview_scene(engine, next_scene_id)

    log_event(
        session_id=session_id,
        event_type="choice",
        scene_id=source_scene_id,
        data={
            "choice_id": payload.choice_id,
            "resulting_scene_id": next_scene_id,
        },
    )

    return SceneResponse(scene=scene, player_state=session["player_state"])


@router.post("/{session_id}/resolve", response_model=SceneResponse)
async def resolve_current_scene(session_id: str, language: str | None = None) -> SceneResponse:
    """Resolve the current scene and update player state."""
    session = _get_session_or_404(session_id)
    if language is not None:
        session["language"] = _normalize_language(language)

    selected_language = _normalize_language(session.get("language"))
    engine = _engine_for_language(selected_language)
    scene_id = str(session["current_scene"])

    scene, updated_state = _resolve_scene_with_state(
        engine,
        session["current_scene"],
        session["player_state"],
    )

    if scene.get("type") == "combat":
        enemy_data = scene.get("raw", {}).get("enemy", {})
        scene["enemy_preview"] = {
            "name": engine.translate(enemy_data.get("name_key", "")),
            "hp": enemy_data.get("hp"),
            "attack": enemy_data.get("attack"),
            "defense": enemy_data.get("defense"),
        }

        combat_result = scene.get("combat_result", {})
        if isinstance(combat_result, dict) and combat_result.get("winner") == "Player":
            stats = updated_state.setdefault("stats", {})
            stats["attack"] = int(stats.get("attack", 0)) + 1

            tag = scene.get("raw", {}).get("analytics", {}).get("tag")
            if tag == "boss":
                stats["defense"] = int(stats.get("defense", 0)) + 1

            scene["player_state"] = updated_state

    session["player_state"] = updated_state

    scene_type = str(scene.get("type", "resolved"))
    event_type = scene_type if scene_type in RESOLVE_EVENT_TYPES else "resolved"
    log_event(
        session_id=session_id,
        event_type=event_type,
        scene_id=scene_id,
        data=_build_resolve_log_data(scene, updated_state),
    )

    if isinstance(scene.get("next_scene"), str):
        session["current_scene"] = scene["next_scene"]

    return SceneResponse(scene=scene, player_state=updated_state)
