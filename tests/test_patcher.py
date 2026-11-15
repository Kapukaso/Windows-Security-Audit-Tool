"""
tests/test_patcher.py
Hermetic unit tests for security/patcher.py (Automated Bi-Weekly Application Patching).
Covers winget discovery, output parsing, active process avoidance, package pinning,
Task Scheduler registration/toggling, upgrade execution workflows, and database audit logs.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

import database.database as db_mod
import security.patcher as patcher_mod
from app import app, ACTIVE_API_KEY, STATE_LOCK, PATCHER_PROGRESS
from security.patcher import (
    is_winget_available,
    get_winget_bootstrap_command,
    is_metered_connection,
    get_running_process_names,
    is_package_in_use,
    parse_winget_upgrade_output,
    get_updatable_packages,
    pin_package,
    unpin_package,
    get_pins,
    get_recommended_pins,
    execute_upgrades,
    get_scheduler_status,
    register_biweekly_task,
    toggle_scheduler_task,
    unregister_scheduler_task,
    TASK_NAME
)


SAMPLE_WINGET_TABLE = """
Name                  Id                          Version        Available    Source
--------------------------------------------------------------------------------------
Google Chrome         Google.Chrome               120.0.6099.130 121.0.6167.85 winget
Discord               Discord.Discord             1.0.9030       1.0.9032      winget
Mozilla Firefox       Mozilla.Firefox             121.0          122.0         winget
3 upgrades available.
"""

SAMPLE_WINGET_EMPTY = """
No applicable upgrade found.
"""


def test_is_winget_available(monkeypatch):
    """Verifies winget detection succeeds when command is found and fails when absent."""
    # Positive path
    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: "C:\\Program Files\\WindowsApps\\winget.exe")
    assert is_winget_available() is True

    # Negative path
    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: "")
    assert is_winget_available() is False


def test_get_winget_bootstrap_command():
    """Verifies bootstrap command contains AppInstaller registration."""
    cmd = get_winget_bootstrap_command()
    assert "Microsoft.DesktopAppInstaller" in cmd
    assert "Add-AppxPackage" in cmd


def test_is_metered_connection(monkeypatch):
    """Verifies metered connection detection handles metered vs unrestricted networks."""
    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: "True")
    assert is_metered_connection() is True

    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: "False")
    assert is_metered_connection() is False


def test_parse_winget_upgrade_output():
    """Verifies tabular winget output is parsed into structured package dictionaries."""
    packages = parse_winget_upgrade_output(SAMPLE_WINGET_TABLE)
    assert len(packages) == 3

    assert packages[0]["name"] == "Google Chrome"
    assert packages[0]["id"] == "Google.Chrome"
    assert packages[0]["version"] == "120.0.6099.130"
    assert packages[0]["available"] == "121.0.6167.85"

    assert packages[1]["name"] == "Discord"
    assert packages[1]["id"] == "Discord.Discord"

    # Empty / non-tabular output
    assert parse_winget_upgrade_output(SAMPLE_WINGET_EMPTY) == []
    assert parse_winget_upgrade_output("") == []
    assert parse_winget_upgrade_output(None) == []


def test_get_updatable_packages(monkeypatch):
    """Verifies updatable packages query returns parsed list when winget is available."""
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: True)
    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: SAMPLE_WINGET_TABLE)

    result = get_updatable_packages()
    assert "packages" in result
    assert len(result["packages"]) == 3

    # Unavailable winget
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: False)
    res_err = get_updatable_packages()
    assert "error" in res_err
    assert res_err["packages"] == []


def test_is_package_in_use():
    """Verifies active running process guard accurately detects in-use applications."""
    running_procs = {"chrome.exe", "discord.exe", "code.exe", "explorer.exe"}

    # Chrome is running
    in_use, matched = is_package_in_use("Google.Chrome", "Google Chrome", running_procs)
    assert in_use is True
    assert matched == "chrome.exe"

    # Discord is running
    in_use, matched = is_package_in_use("Discord.Discord", "Discord", running_procs)
    assert in_use is True
    assert matched == "discord.exe"

    # Firefox is NOT running
    in_use, matched = is_package_in_use("Mozilla.Firefox", "Mozilla Firefox", running_procs)
    assert in_use is False
    assert matched is None


def test_pin_and_unpin_package(in_memory_db, monkeypatch):
    """Verifies hybrid package pinning stores in DB and invokes native winget."""
    mock_ps = MagicMock(return_value="")
    monkeypatch.setattr(patcher_mod, "run_powershell", mock_ps)
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: True)

    # Pin package
    res_pin = pin_package("Python.Python.3.11", "Python 3.11", reason="Developer test pin")
    assert res_pin["success"] is True

    # Winget pin add was called
    mock_ps.assert_called_with('winget pin add --id "Python.Python.3.11" --blocking')

    # Verify present in get_pins()
    pins = get_pins()
    assert len(pins) == 1
    assert pins[0]["package_id"] == "Python.Python.3.11"
    assert pins[0]["reason"] == "Developer test pin"

    # Unpin package
    res_unpin = unpin_package("Python.Python.3.11")
    assert res_unpin["success"] is True
    mock_ps.assert_called_with('winget pin remove --id "Python.Python.3.11"')

    # Verify no longer in DB
    assert len(get_pins()) == 0


def test_get_recommended_pins():
    """Verifies recommended pins list contains essential runtimes."""
    recs = get_recommended_pins()
    assert isinstance(recs, list)
    ids = [r["package_id"] for r in recs]
    assert any("Python" in i for i in ids)
    assert any("NodeJS" in i for i in ids)
    assert any("Git" in i for i in ids)


def test_execute_upgrades_metered_deferred(in_memory_db, monkeypatch):
    """Verifies scheduled execution is deferred on metered networks."""
    monkeypatch.setattr(patcher_mod, "is_metered_connection", lambda: True)

    res = execute_upgrades(trigger_type="SCHEDULED")
    assert res["status"] == "METERED_DEFERRED"
    assert res["success"] is True

    history = db_mod.get_patch_history()
    assert len(history) == 1
    assert history[0]["status"] == "METERED_DEFERRED"


def test_execute_upgrades_no_updates(in_memory_db, monkeypatch):
    """Verifies upgrade returns success when all applications are up to date."""
    monkeypatch.setattr(patcher_mod, "is_metered_connection", lambda: False)
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: True)
    monkeypatch.setattr(patcher_mod, "get_updatable_packages", lambda: {"packages": []})

    res = execute_upgrades(trigger_type="MANUAL")
    assert res["status"] == "SUCCESS"
    assert res["packages_updated"] == 0

    history = db_mod.get_patch_history()
    assert len(history) == 1
    assert history[0]["status"] == "SUCCESS"


def test_execute_upgrades_full_flow(in_memory_db, monkeypatch):
    """
    Verifies full execution lifecycle:
    - Discord is active -> SKIPPED_IN_USE
    - Python is pinned -> SKIPPED_PINNED
    - Mozilla Firefox is eligible -> UPDATED
    - Broken App fails -> FAILED (overall status PARTIAL)
    """
    monkeypatch.setattr(patcher_mod, "is_metered_connection", lambda: False)
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: True)

    # Pin Python in DB
    db_mod.add_pinned_package("Python.Python.3.11", "Python 3.11", reason="Pinned runtime")

    # Mock updatable packages
    mock_packages = [
        {"name": "Discord", "id": "Discord.Discord", "version": "1.0", "available": "1.1"},
        {"name": "Python 3.11", "id": "Python.Python.3.11", "version": "3.11.0", "available": "3.11.1"},
        {"name": "Mozilla Firefox", "id": "Mozilla.Firefox", "version": "120.0", "available": "121.0"},
        {"name": "Broken App", "id": "Vendor.BrokenApp", "version": "2.0", "available": "2.1"}
    ]
    monkeypatch.setattr(patcher_mod, "get_updatable_packages", lambda: {"packages": mock_packages})

    # Mock running processes (Discord is running)
    monkeypatch.setattr(patcher_mod, "get_running_process_names", lambda: {"discord.exe"})

    def mock_run_powershell(cmd):
        if "Mozilla.Firefox" in cmd:
            return "Successfully installed Mozilla Firefox"
        elif "Vendor.BrokenApp" in cmd:
            return "Installer failed with exit code -1978335212"
        return ""

    monkeypatch.setattr(patcher_mod, "run_powershell", mock_run_powershell)

    callback_messages = []
    def progress_cb(msg, pct):
        callback_messages.append((msg, pct))

    res = execute_upgrades(trigger_type="MANUAL", progress_callback=progress_cb)

    assert res["status"] == "PARTIAL"
    assert res["packages_updated"] == 1
    assert res["packages_skipped"] == 2
    assert res["packages_failed"] == 1
    assert len(callback_messages) > 0

    # Verify audit history
    history = db_mod.get_patch_history()
    assert len(history) == 1
    assert history[0]["status"] == "PARTIAL"
    assert history[0]["packages_updated"] == 1
    assert history[0]["packages_skipped"] == 2
    assert history[0]["packages_failed"] == 1


def test_task_scheduler_status_and_lifecycle(monkeypatch):
    """Verifies get_scheduler_status, register_biweekly_task, toggle, and unregister."""
    # Mock task status response
    mock_json = {
        "task_exists": True,
        "task_name": TASK_NAME,
        "state": "Ready",
        "last_run": "2026-11-10 03:00:00",
        "next_run": "2026-11-24 03:00:00",
        "last_result": 0
    }
    monkeypatch.setattr(patcher_mod, "run_powershell_json", lambda cmd: mock_json)

    status = get_scheduler_status()
    assert status["task_exists"] is True
    assert status["state"] == "Ready"
    assert status["next_run"] == "2026-11-24 03:00:00"

    # Register task command execution
    mock_ps = MagicMock(return_value="")
    monkeypatch.setattr(patcher_mod, "run_powershell", mock_ps)
    res_reg = register_biweekly_task()
    assert res_reg["task_exists"] is True
    assert mock_ps.call_count >= 1

    # Toggle task
    res_toggle = toggle_scheduler_task(enabled=False)
    assert res_toggle["task_exists"] is True

    # Unregister task
    res_unreg = unregister_scheduler_task()
    assert res_unreg["success"] is True


# ==========================================
# REST API & HUD UI Integration Tests
# ==========================================

@pytest.fixture
def client():
    """Provides a Flask test client configured for testing."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_api_patcher_status(client, in_memory_db, monkeypatch):
    """Verifies GET /api/patcher/status returns health and telemetry metadata."""
    monkeypatch.setattr(patcher_mod, "is_winget_available", lambda: True)
    monkeypatch.setattr(patcher_mod, "get_updatable_packages", lambda: {"packages": [{"id": "Test.Pkg", "name": "Test"}]})
    monkeypatch.setattr(patcher_mod, "get_scheduler_status", lambda: {"task_exists": True, "state": "Ready"})

    res = client.get("/api/patcher/status")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["winget_available"] is True
    assert data["updatable_count"] == 1
    assert data["scheduler"]["task_exists"] is True


def test_api_patcher_auth_protection(client):
    """Verifies all mutating patcher endpoints reject unauthenticated requests with HTTP 401."""
    mutating_requests = [
        ("POST", "/api/patcher/schedule", {"enabled": True}),
        ("POST", "/api/patcher/run-now", {}),
        ("POST", "/api/patcher/pin", {"package_id": "Test.App"}),
        ("DELETE", "/api/patcher/pin/Test.App", None)
    ]
    for method, path, payload in mutating_requests:
        if method == "POST":
            res = client.post(path, json=payload)
        else:
            res = client.delete(path)
        assert res.status_code == 401, f"{method} {path} should require authentication"
        data = res.get_json()
        assert data["success"] is False
        assert "Unauthorized" in data["error"]


def test_api_patcher_schedule_authenticated(client, monkeypatch):
    """Verifies authenticated POST /api/patcher/schedule toggles scheduled task."""
    monkeypatch.setattr(patcher_mod, "toggle_scheduler_task", lambda enabled: {"task_exists": True, "state": "Ready" if enabled else "Disabled"})

    headers = {"X-Defiant-Key": ACTIVE_API_KEY}
    res = client.post("/api/patcher/schedule", headers=headers, json={"enabled": True})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["scheduler"]["state"] == "Ready"


def test_api_patcher_run_now_and_progress(client, monkeypatch):
    """Verifies on-demand patch execution and concurrency conflict handling (409)."""
    monkeypatch.setattr(patcher_mod, "execute_upgrades", lambda trigger_type, progress_callback: {"success": True})

    headers = {"X-Defiant-Key": ACTIVE_API_KEY}

    # Reset patcher state
    with STATE_LOCK:
        PATCHER_PROGRESS["status"] = "idle"
        PATCHER_PROGRESS["percentage"] = 0

    # Trigger run-now
    res = client.post("/api/patcher/run-now", headers=headers)
    assert res.status_code == 200
    assert res.get_json()["success"] is True

    # Simulate in-progress state to verify conflict detection (409)
    with STATE_LOCK:
        PATCHER_PROGRESS["status"] = "running"

    res_conflict = client.post("/api/patcher/run-now", headers=headers)
    assert res_conflict.status_code == 409
    assert res_conflict.get_json()["success"] is False

    # Check progress endpoint
    res_prog = client.get("/api/patcher/progress")
    assert res_prog.status_code == 200
    assert res_prog.get_json()["status"] == "running"

    # Clean up state
    with STATE_LOCK:
        PATCHER_PROGRESS["status"] = "idle"


def test_api_patcher_pins_crud_and_history(client, in_memory_db, monkeypatch):
    """Verifies pinning CRUD and patch history retrieval via API."""
    monkeypatch.setattr(patcher_mod, "run_powershell", lambda cmd: "")
    headers = {"X-Defiant-Key": ACTIVE_API_KEY}

    # Get initial pins
    res_pins = client.get("/api/patcher/pins")
    assert res_pins.status_code == 200
    data_pins = res_pins.get_json()
    assert data_pins["success"] is True
    assert len(data_pins["recommended"]) > 0

    # Add pin
    res_add = client.post(
        "/api/patcher/pin",
        headers=headers,
        json={"package_id": "Git.Git", "package_name": "Git SCM", "reason": "Test Pin"}
    )
    assert res_add.status_code == 200
    assert res_add.get_json()["success"] is True

    # Verify pin is listed
    res_list = client.get("/api/patcher/pins")
    pins = res_list.get_json()["pins"]
    assert any(p["package_id"] == "Git.Git" for p in pins)

    # Remove pin
    res_del = client.delete("/api/patcher/pin/Git.Git", headers=headers)
    assert res_del.status_code == 200
    assert res_del.get_json()["success"] is True

    # Check history endpoint
    res_hist = client.get("/api/patcher/history")
    assert res_hist.status_code == 200
    assert "history" in res_hist.get_json()


def test_dashboard_ui_patcher_elements(client):
    """Verifies that templates/dashboard.html renders all required Auto-Patcher HUD controls."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Check Sidebar navigation item
    assert 'id="nav-patcher"' in html
    assert "Auto-Patcher" in html

    # Check View Container
    assert 'id="view-patcher"' in html
    assert "AUTOMATED APPLICATION PATCHER" in html
    assert 'id="winget-alert-banner"' in html
    assert 'id="patcher-progress-container"' in html
    assert 'id="patchNowBtn"' in html
    assert 'id="toggleScheduleBtn"' in html

    # Check Pinning and Audit Table elements
    assert 'id="recommended-pins-container"' in html
    assert 'id="custom-pin-id"' in html
    assert 'id="patcher-pins-tbody"' in html
    assert 'id="patcher-history-tbody"' in html

    # Check JavaScript functions exist
    assert "loadPatcherStatus" in html
    assert "runManualPatcher" in html
    assert "handleScheduleToggle" in html
    assert "loadPatcherPins" in html
    assert "loadPatcherHistory" in html

