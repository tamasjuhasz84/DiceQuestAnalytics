"""Integration tests for FastAPI game and analytics endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes.game_routes import sessions


@pytest.fixture(autouse=True)
def clear_sessions() -> None:
    """Ensure each test starts with a clean in-memory session store."""
    sessions.clear()


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_start_game_with_english_language(client: TestClient) -> None:
    response = client.post("/game/start", params={"language": "en"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["start_scene"]["title"] == "The Tower Gate"


def test_scene_can_switch_language_mid_session(client: TestClient) -> None:
    start = client.post("/game/start", params={"language": "hu"}).json()
    session_id = start["session_id"]

    scene_en = client.get(f"/game/{session_id}/scene", params={"language": "en"})

    assert scene_en.status_code == 200
    assert scene_en.json()["scene"]["title"] == "The Tower Gate"


def test_invalid_choice_returns_400(client: TestClient) -> None:
    start = client.post("/game/start").json()
    session_id = start["session_id"]

    response = client.post(
        f"/game/{session_id}/choice",
        json={"choice_id": "does_not_exist"},
    )

    assert response.status_code == 400


def test_missing_session_returns_404(client: TestClient) -> None:
    response = client.get("/game/not-a-real-session/scene")
    assert response.status_code == 404


def test_resolve_advances_session_from_dice_scene(client: TestClient) -> None:
    start = client.post("/game/start").json()
    session_id = start["session_id"]

    # intro_01 -> go_around -> intro_03 (dice_check scene)
    choose = client.post(
        f"/game/{session_id}/choice",
        json={"choice_id": "go_around"},
    )
    assert choose.status_code == 200
    assert choose.json()["scene"]["id"] == "intro_03"

    resolved = client.post(f"/game/{session_id}/resolve")
    assert resolved.status_code == 200
    resolved_scene = resolved.json()["scene"]
    assert "check_result" in resolved_scene
    assert isinstance(resolved_scene.get("next_scene"), str)

    current = client.get(f"/game/{session_id}/scene")
    assert current.status_code == 200
    assert current.json()["scene"]["id"] == resolved_scene["next_scene"]


def test_analytics_summary_endpoint(client: TestClient) -> None:
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "total_games" in payload
    assert "win_rate" in payload
