"""
tests/test_api.py
Automated integration tests for Flask Web API endpoints (app.py).
Validates UI rendering, @require_auth security enforcement (401),
STATE_LOCK concurrency conflict handling (409), and endpoint operations.
"""
from unittest.mock import patch, MagicMock
import pytest

from app import app, ACTIVE_API_KEY, STATE_LOCK, SCAN_PROGRESS


@pytest.fixture
def client():
    """Provides a Flask test client configured for testing."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_index_route(client):
    """Verifies the root route renders the dashboard HTML."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Defiant" in html or "Dashboard" in html or "Security" in html


def test_require_auth_missing_header(client):
    """Verifies mutating endpoints reject unauthenticated requests with HTTP 401."""
    mutating_endpoints = [
        ("/api/remediate/execute", {"finding_id": "POL-001"}),
        ("/api/remediate/rollback", {"finding_id": "POL-001"}),
        ("/api/fim/reset", {}),
        ("/api/shutdown", {})
    ]
    for endpoint, payload in mutating_endpoints:
        response = client.post(endpoint, json=payload)
        assert response.status_code == 401, f"{endpoint} did not return 401"
        data = response.get_json()
        assert data["success"] is False
        assert "Unauthorized" in data["error"]


def test_require_auth_invalid_header(client):
    """Verifies mutating endpoints reject forged or invalid API keys."""
    # Invalid X-Defiant-Key header
    res_key = client.post(
        "/api/remediate/execute",
        headers={"X-Defiant-Key": "forged_invalid_api_key_12345"},
        json={"finding_id": "POL-001"}
    )
    assert res_key.status_code == 401

    # Invalid Bearer token
    res_bearer = client.post(
        "/api/remediate/execute",
        headers={"Authorization": "Bearer forged_token_abcde"},
        json={"finding_id": "POL-001"}
    )
    assert res_bearer.status_code == 401


def test_require_auth_valid_header(client, in_memory_db, mock_subprocess):
    """Verifies requests with valid API key or Bearer token succeed."""
    # Valid X-Defiant-Key header
    res_key = client.post(
        "/api/remediate/execute",
        headers={"X-Defiant-Key": ACTIVE_API_KEY},
        json={"finding_id": "POL-001"}
    )
    assert res_key.status_code == 200
    data_key = res_key.get_json()
    assert data_key["success"] is True

    # Valid Bearer token
    res_bearer = client.post(
        "/api/remediate/rollback",
        headers={"Authorization": f"Bearer {ACTIVE_API_KEY}"},
        json={"finding_id": "POL-001"}
    )
    assert res_bearer.status_code == 200
    data_bearer = res_bearer.get_json()
    assert data_bearer["success"] is True


def test_scan_progress_polling(client):
    """Verifies /api/scan/progress returns the active scan status safely."""
    response = client.get("/api/scan/progress")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "percentage" in data
    assert "message" in data


def test_scan_concurrency_conflict(client):
    """Verifies concurrent scan attempts trigger HTTP 409 Conflict."""
    with STATE_LOCK:
        original_status = SCAN_PROGRESS["status"]
        SCAN_PROGRESS["status"] = "running"
        SCAN_PROGRESS["message"] = "Active audit in progress..."

    try:
        response = client.post("/api/scan")
        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False
        assert "already in progress" in data["error"]
    finally:
        with STATE_LOCK:
            SCAN_PROGRESS["status"] = original_status


def test_remediate_preview_endpoint(client):
    """Verifies preview endpoint returns metadata without requiring auth."""
    response = client.post("/api/remediate/preview", json={"finding_id": "POL-001"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["supported"] is True
    assert data["finding_id"] == "POL-001"


def test_remediate_history_endpoint(client, in_memory_db):
    """Verifies remediation history endpoint returns list of past events."""
    response = client.get("/api/remediate/history")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["history"], list)


def test_telemetry_endpoint(client, in_memory_db):
    """Verifies live telemetry returns CPU and RAM data and records to DB."""
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "cpu_percent" in data
    assert "ram_percent" in data


def test_history_endpoint(client, in_memory_db):
    """Verifies past audit history endpoint returns scan list."""
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert isinstance(data["history"], list)


def test_fim_reset_endpoint(client, in_memory_db):
    """Verifies FIM baseline reset endpoint clears records when authorized."""
    response = client.post(
        "/api/fim/reset",
        headers={"X-Defiant-Key": ACTIVE_API_KEY}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert "reset" in data["message"].lower()


def test_shutdown_endpoint(client):
    """Verifies shutdown endpoint acknowledges request when authenticated."""
    with patch("os.kill") as mock_kill:
        response = client.post(
            "/api/shutdown",
            headers={"X-Defiant-Key": ACTIVE_API_KEY}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "shutting down" in data["message"].lower()
        assert mock_kill.called
