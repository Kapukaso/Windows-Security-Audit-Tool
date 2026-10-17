"""
tests/test_remediation.py
Automated unit tests for security/remediation.py.
Verifies playbook structures, preview generation, approval enforcement,
safe-only policy restrictions, execution dispatch, and rollback logging.
"""
import pytest
from unittest.mock import MagicMock

from security.remediation import (
    PLAYBOOKS,
    get_remediation_preview,
    execute_remediation,
    rollback_remediation,
    get_remediation_history,
    log_remediation_action
)


def test_playbooks_registry_structure():
    """Verifies all expected playbooks are registered with valid schemas."""
    expected_playbooks = {
        "POL-001",
        "POL-002",
        "NET-001",
        "NET-002",
        "NET-ISOLATE",
        "DEF-001",
        "FW-001"
    }
    assert expected_playbooks.issubset(PLAYBOOKS.keys())

    for pb_id, pb in PLAYBOOKS.items():
        assert pb["finding_id"] == pb_id
        assert "description" in pb
        assert pb["risk_level"] in ("SAFE", "MEDIUM", "HIGH")
        assert "preview" in pb
        assert "execute_cmd" in pb
        assert "rollback_cmd" in pb
        assert pb["type"] in ("subprocess", "powershell")


def test_remediation_preview():
    """Tests preview generation and approval requirements."""
    # Unknown finding
    unknown = get_remediation_preview("NONEXISTENT-999")
    assert unknown["supported"] is False

    # SAFE finding (no approval required)
    safe_prev = get_remediation_preview("POL-001")
    assert safe_prev["supported"] is True
    assert safe_prev["risk_level"] == "SAFE"
    assert safe_prev["requires_approval"] is False

    # MEDIUM finding (requires approval)
    med_prev = get_remediation_preview("NET-001")
    assert med_prev["supported"] is True
    assert med_prev["risk_level"] == "MEDIUM"
    assert med_prev["requires_approval"] is True

    # HIGH finding (requires approval)
    high_prev = get_remediation_preview("NET-002")
    assert high_prev["supported"] is True
    assert high_prev["risk_level"] == "HIGH"
    assert high_prev["requires_approval"] is True


def test_remediation_approval_enforcement(in_memory_db, mock_powershell):
    """Verifies MEDIUM/HIGH actions are blocked without explicit approval."""
    # 1. Blocked without approval
    result = execute_remediation("NET-002", approval_granted=False)
    assert result["success"] is False
    assert result.get("requires_approval") is True
    assert "blocked" in result["message"].lower()

    history = get_remediation_history()
    assert len(history) >= 1
    assert history[0]["finding_id"] == "NET-002"
    assert history[0]["action_type"] == "EXECUTE"
    assert history[0]["status"] == "BLOCKED"

    # 2. Allowed with explicit approval
    result_approved = execute_remediation("NET-002", approval_granted=True)
    assert result_approved["success"] is True
    assert mock_powershell.called

    history_updated = get_remediation_history()
    assert history_updated[0]["finding_id"] == "NET-002"
    assert history_updated[0]["action_type"] == "EXECUTE"
    assert history_updated[0]["status"] == "SUCCESS"


def test_remediation_safe_only_policy(in_memory_db):
    """Verifies that safe_only_policy blocks MEDIUM/HIGH actions even if approved."""
    result = execute_remediation("NET-001", approval_granted=True, safe_only_policy=True)
    assert result["success"] is False
    assert "Safe Only" in result["message"]

    history = get_remediation_history()
    assert len(history) >= 1
    assert history[0]["finding_id"] == "NET-001"
    assert history[0]["status"] == "BLOCKED"


def test_remediation_safe_execution(in_memory_db, mock_subprocess):
    """Verifies SAFE actions execute without requiring explicit approval."""
    result = execute_remediation("POL-001", approval_granted=False)
    assert result["success"] is True
    assert mock_subprocess.called

    history = get_remediation_history()
    assert history[0]["finding_id"] == "POL-001"
    assert history[0]["status"] == "SUCCESS"


def test_rollback_execution(in_memory_db, mock_subprocess):
    """Verifies rollback command dispatch and audit logging."""
    # Unknown rollback
    bad_rollback = rollback_remediation("UNKNOWN-000")
    assert bad_rollback["success"] is False

    # Valid rollback
    result = rollback_remediation("POL-001")
    assert result["success"] is True
    assert mock_subprocess.called

    history = get_remediation_history()
    assert history[0]["finding_id"] == "POL-001"
    assert history[0]["action_type"] == "ROLLBACK"
    assert history[0]["status"] == "SUCCESS"


def test_remediation_history_ordering(in_memory_db):
    """Verifies remediation history retrieves records in reverse chronological order."""
    log_remediation_action("POL-001", "EXECUTE", "SUCCESS", "First action")
    log_remediation_action("NET-002", "EXECUTE", "BLOCKED", "Second action")
    log_remediation_action("POL-001", "ROLLBACK", "SUCCESS", "Third action")

    history = get_remediation_history()
    assert len(history) >= 3
    assert history[0]["action_type"] == "ROLLBACK"
    assert history[1]["status"] == "BLOCKED"
    assert history[2]["message"] == "First action"
