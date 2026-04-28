"""Pydantic schemas for API requests/responses."""

from typing import Any

from pydantic import BaseModel


class ChoiceRequest(BaseModel):
    """Request payload for selecting a choice in the current scene."""

    choice_id: str


class StartGameResponse(BaseModel):
    """Response payload after starting a game session."""

    session_id: str
    start_scene: dict[str, Any]
    player_state: dict[str, Any]


class SceneResponse(BaseModel):
    """Response payload with current or resolved scene and updated player state."""

    scene: dict[str, Any]
    player_state: dict[str, Any]
