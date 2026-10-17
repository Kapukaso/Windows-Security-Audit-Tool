"""
tests/conftest.py
Shared hermetic mock fixtures for Defiant (Windows Security Audit Tool).
Guarantees 100% offline, elevation-free, fast test execution.
"""
import os
import json
import sqlite3
import tempfile
import subprocess
from unittest.mock import MagicMock
import pytest

import database.database as db_mod
import security.remediation as rem_mod


@pytest.fixture(autouse=True)
def mock_fast_timers(monkeypatch):
    """
    Globally intercepts psutil.cpu_percent across all tests
    to eliminate artificial 1-second interval delays.
    """
    import psutil
    monkeypatch.setattr(psutil, "cpu_percent", lambda *args, **kwargs: 12.5)


@pytest.fixture
def in_memory_db(monkeypatch):
    """
    Provides an isolated SQLite database using a dedicated temporary database file.
    Guarantees production audit_history.db is never touched or modified.
    """
    tmp_fd, tmp_file = tempfile.mkstemp(suffix="_test_defiant.db")
    os.close(tmp_fd)

    def connection_factory():
        return sqlite3.connect(tmp_file, check_same_thread=False)

    monkeypatch.setattr(db_mod, "get_connection", connection_factory)
    monkeypatch.setattr(rem_mod, "get_connection", connection_factory)
    monkeypatch.setattr(db_mod, "SQLITE_PATH", tmp_file)
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_file)
    monkeypatch.setattr(db_mod, "DB_ENGINE", "sqlite")
    monkeypatch.setattr(rem_mod, "DB_ENGINE", "sqlite")

    db_mod.init_db()
    conn = connection_factory()

    yield conn

    conn.close()
    try:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
    except Exception:
        pass


@pytest.fixture
def mock_powershell(monkeypatch):
    """
    Mocks utils.powershell.run_powershell_json and its imported references
    across all audit modules.
    """
    mock = MagicMock(return_value=[])
    monkeypatch.setattr("utils.powershell.run_powershell_json", mock)

    audit_mods = [
        "modules.defender",
        "modules.drivers",
        "modules.event_logs",
        "modules.firewall",
        "modules.registry",
        "modules.software",
        "modules.startup",
        "modules.updates",
        "modules.users",
        "security.remediation"
    ]
    for mod_name in audit_mods:
        try:
            monkeypatch.setattr(f"{mod_name}.run_powershell_json", mock)
        except (AttributeError, KeyError):
            pass

    return mock


@pytest.fixture
def mock_subprocess(monkeypatch):
    """
    Mocks subprocess.run for net accounts and remediation command executions.
    """
    mock = MagicMock()
    mock.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="",
        stderr=""
    )
    monkeypatch.setattr("subprocess.run", mock)
    
    for mod_name in ["modules.password_policy", "security.remediation"]:
        try:
            monkeypatch.setattr(f"{mod_name}.subprocess.run", mock)
        except (AttributeError, KeyError):
            pass

    return mock


@pytest.fixture
def mock_wintrust(monkeypatch):
    """
    Mocks security.verification.WinVerifyTrust ctypes binding.
    Default return 0 corresponds to ERROR_SUCCESS (validly signed binary).
    """
    mock = MagicMock(return_value=0)
    monkeypatch.setattr("security.verification.WinVerifyTrust", mock)
    return mock


@pytest.fixture
def mock_nvd_urlopen(monkeypatch):
    """
    Mocks urllib.request.urlopen for NIST NVD and CrowdStrike queries.
    """
    def _create_mock_response(payload, status=200):
        resp = MagicMock()
        resp.read.return_value = json.dumps(payload).encode("utf-8")
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = None
        resp.status = status
        return resp

    mock_open = MagicMock(return_value=_create_mock_response({"vulnerabilities": []}))
    monkeypatch.setattr("urllib.request.urlopen", mock_open)
    return mock_open
