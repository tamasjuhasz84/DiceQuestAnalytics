"""Small API client helpers for Streamlit pages."""

from __future__ import annotations

import os
from typing import Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT_SECONDS = 10


class ApiError(Exception):
    """Raised when backend communication fails."""


def _request(
    method: str,
    path: str,
    json_data: dict[str, Any] | None = None,
    query_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{API_BASE_URL}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            params=query_params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise ApiError(f"Could not reach backend at {API_BASE_URL}. Details: {exc}") from exc

    if response.status_code >= 400:
        detail = "Unknown error"
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = str(payload.get("detail", detail))
        except ValueError:
            detail = response.text or detail

        raise ApiError(f"Backend error ({response.status_code}): {detail}")

    try:
        data = response.json()
    except ValueError as exc:
        raise ApiError("Backend returned invalid JSON response") from exc

    if not isinstance(data, dict):
        raise ApiError("Backend response must be a JSON object")

    return data


def start_game(language: str = "hu") -> dict[str, Any]:
    """Start a new game session."""
    return _request("POST", "/game/start", query_params={"language": language})


def get_scene(session_id: str, language: str = "hu") -> dict[str, Any]:
    """Fetch current scene for an existing session."""
    return _request("GET", f"/game/{session_id}/scene", query_params={"language": language})


def submit_choice(session_id: str, choice_id: str, language: str = "hu") -> dict[str, Any]:
    """Submit a choice for the current scene."""
    return _request(
        "POST",
        f"/game/{session_id}/choice",
        {"choice_id": choice_id},
        query_params={"language": language},
    )


def resolve_scene(session_id: str, language: str = "hu") -> dict[str, Any]:
    """Resolve the current scene (dice/combat/random/effects)."""
    return _request("POST", f"/game/{session_id}/resolve", query_params={"language": language})


def get_analytics_summary() -> dict[str, Any]:
    """Fetch summary analytics metrics."""
    return _request("GET", "/analytics/summary")


def get_analytics_choices() -> dict[str, Any]:
    """Fetch choice distribution analytics."""
    return _request("GET", "/analytics/choices")


def get_analytics_deaths() -> dict[str, Any]:
    """Fetch death reason analytics."""
    return _request("GET", "/analytics/deaths")


def get_analytics_scenes() -> dict[str, Any]:
    """Fetch scene popularity analytics."""
    return _request("GET", "/analytics/scenes")


def get_analytics_dice() -> dict[str, Any]:
    """Fetch dice analytics."""
    return _request("GET", "/analytics/dice")


def get_analytics_combat() -> dict[str, Any]:
    """Fetch combat analytics."""
    return _request("GET", "/analytics/combat")
