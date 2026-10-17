"""
tests/test_audit_modules.py
Comprehensive unit and mock tests across all 16 audit and collection modules in modules/.
Verifies compliant states, risk detection, and failure fallbacks without live elevation.
"""
import os
import json
import datetime
from unittest.mock import MagicMock, patch
import pytest

from modules.defender import get_defender_status, assess_defender, defender_score
from modules.firewall import get_firewall_status, assess_firewall, firewall_score
from modules.users import get_local_users, assess_users, user_score
from modules.password_policy import get_password_policy, assess_password_policy
from modules.software import get_installed_software, analyze_software_risk
from modules.cve_lookup import query_nvd_api, audit_software_cves, NVDCircuitBreaker
from modules.services import get_services, assess_services
from modules.ports import get_listening_ports, assess_ports
from modules.startup import get_startup_apps, assess_startup
from modules.updates import get_windows_updates, assess_updates
from modules.event_logs import get_event_log_stats, assess_event_logs
from modules.fim import audit_fim
from modules.drivers import get_drivers, assess_drivers
from modules.registry import get_registry_security, assess_registry
from modules.ml_anomaly import generate_training_baseline, audit_anomalies
from modules.threat_intel import fetch_crowdstrike_iocs, scan_threat_intel, LOCAL_IOC_DATABASE
from modules.compliance import generate_compliance_report
from modules.system import get_system_info
from modules.report import generate_json_report, generate_html_report


# ==============================================================================
# 1. DEFENDER MODULE
# ==============================================================================

def test_defender_module_compliant():
    status = {
        "AntivirusEnabled": True,
        "RealTimeProtectionEnabled": True,
        "BehaviorMonitorEnabled": True,
        "IoavProtectionEnabled": True,
        "NISEnabled": True
    }
    findings = assess_defender(status)
    assert len(findings) == 0
    score = defender_score(status)
    assert score == 10


def test_defender_module_findings():
    status = {
        "AntivirusEnabled": False,
        "RealTimeProtectionEnabled": False,
        "BehaviorMonitorEnabled": True,
        "IoavProtectionEnabled": True,
        "NISEnabled": True
    }
    findings = assess_defender(status)
    finding_ids = {f["id"] for f in findings}
    assert "DEF-001" in finding_ids
    assert "DEF-002" in finding_ids
    score = defender_score(status)
    assert score == 6


def test_defender_module_fallback(mock_powershell):
    mock_powershell.return_value = {"error": "PowerShell execution failed"}
    status = get_defender_status()
    assert "error" in status
    findings = assess_defender(status)
    assert len(findings) >= 1
    assert findings[0]["id"] == "DEF-ERR"


# ==============================================================================
# 2. FIREWALL MODULE
# ==============================================================================

def test_firewall_module_compliant():
    status = [
        {"Name": "Domain", "Enabled": True},
        {"Name": "Private", "Enabled": True},
        {"Name": "Public", "Enabled": True}
    ]
    findings = assess_firewall(status)
    assert len(findings) == 0
    score = firewall_score(status)
    assert score == 10


def test_firewall_module_findings():
    status = [
        {"Name": "Domain", "Enabled": True},
        {"Name": "Private", "Enabled": False},
        {"Name": "Public", "Enabled": False}
    ]
    findings = assess_firewall(status)
    assert len(findings) == 2
    assert findings[0]["id"] == "FW-001"
    score = firewall_score(status)
    assert score == 3


def test_firewall_module_fallback(mock_powershell):
    mock_powershell.return_value = {"error": "Access Denied"}
    status = get_firewall_status()
    assert "error" in status
    findings = assess_firewall(status)
    assert len(findings) >= 1
    assert findings[0]["id"] == "FW-ERR"


# ==============================================================================
# 3. USERS MODULE
# ==============================================================================

def test_users_module_compliant():
    users = [
        {"Name": "Administrator", "Enabled": False, "IsAdministrator": True},
        {"Name": "Guest", "Enabled": False, "IsAdministrator": False},
        {"Name": "DefaultAccount", "Enabled": False, "IsAdministrator": False},
        {"Name": "WDAGUtilityAccount", "Enabled": False, "IsAdministrator": False},
        {"Name": "SecOpsUser", "Enabled": True, "IsAdministrator": True}
    ]
    findings = assess_users(users)
    assert len(findings) == 0
    score = user_score(users)
    assert score == 10


def test_users_module_findings():
    users = [
        {"Name": "Guest", "Enabled": True, "IsAdministrator": False},
        {"Name": "Admin1", "Enabled": True, "IsAdministrator": True},
        {"Name": "Admin2", "Enabled": True, "IsAdministrator": True},
        {"Name": "Admin3", "Enabled": True, "IsAdministrator": True}
    ]
    findings = assess_users(users)
    finding_ids = {f["id"] for f in findings}
    assert "USR-001" in finding_ids
    assert "USR-002" in finding_ids
    score = user_score(users)
    assert score < 10


def test_users_module_fallback(mock_powershell):
    mock_powershell.return_value = {"error": "Failed"}
    users = get_local_users()
    assert "error" in users
    findings = assess_users(users)
    assert len(findings) >= 1
    assert findings[0]["id"] == "USR-ERR"


# ==============================================================================
# 4. PASSWORD POLICY MODULE
# ==============================================================================

def test_password_policy_module_compliant():
    policy = {
        "Minimum password length": "14",
        "Maximum password age (days)": "90",
        "Lockout threshold": "5"
    }
    findings = assess_password_policy(policy)
    assert len(findings) == 0


def test_password_policy_module_findings():
    policy = {
        "Minimum password length": "6",
        "Maximum password age (days)": "Never",
        "Lockout threshold": "Never"
    }
    findings = assess_password_policy(policy)
    finding_ids = {f["id"] for f in findings}
    assert "POL-001" in finding_ids
    assert "POL-002" in finding_ids


def test_password_policy_module_fallback(mock_subprocess):
    import subprocess
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "net accounts")
    policy = get_password_policy()
    assert "error" in policy


# ==============================================================================
# 5. SOFTWARE & CVE LOOKUP MODULES
# ==============================================================================

def test_software_module_assessment():
    software_list = [
        {"Name": "Google Chrome", "Version": "120.0.6099.130", "Publisher": "Google LLC"},
        {"Name": "Unsigned Utility", "Version": "1.0.0", "Publisher": "Unknown"},
        {"Name": "Wireshark Network Tool", "Version": "4.2.0", "Publisher": "Wireshark"}
    ]
    findings = analyze_software_risk(software_list)
    finding_ids = {f["id"] for f in findings}
    assert "SOFT-001" in finding_ids
    assert "SOFT-002" in finding_ids


def test_cve_lookup_cached_hit(in_memory_db, monkeypatch):
    from database.database import save_cve_cache
    app_name = "VulnerableTestApp"
    version = "1.0.0"
    mock_cves = [
        {
            "cve": {
                "id": "CVE-2026-12345",
                "descriptions": [{"value": "Buffer overflow in test application."}]
            }
        }
    ]
    save_cve_cache(app_name, version, mock_cves)

    # Disable network so any network call would fail
    monkeypatch.setattr("urllib.request.urlopen", MagicMock(side_effect=AssertionError("Network accessed!")))
    monkeypatch.setattr("time.sleep", lambda *args: None)

    findings = audit_software_cves([{"Name": app_name, "Version": version}])
    assert len(findings) == 1
    assert findings[0]["id"] == f"CVE|{app_name}"
    assert "CVE-2026-12345" in findings[0]["description"]


def test_cve_circuit_breaker_on_rate_limit(in_memory_db, monkeypatch):
    import urllib.error
    monkeypatch.setattr("time.sleep", lambda *args: None)

    def mock_429(*args, **kwargs):
        raise urllib.error.HTTPError("http://nvd", 429, "Too Many Requests", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", mock_429)

    findings = audit_software_cves([{"Name": "UncachedAppA", "Version": "2.0"}, {"Name": "UncachedAppB", "Version": "3.0"}])
    warning_findings = [f for f in findings if f["id"] == "CVE-NVD-UNAVAILABLE"]
    assert len(warning_findings) == 1
    assert "Rate limited" in warning_findings[0]["description"]


# ==============================================================================
# 6. SERVICES MODULE
# ==============================================================================

def test_services_module_compliant():
    services = [
        {
            "Name": "W32Time",
            "DisplayName": "Windows Time",
            "BinPath": r"C:\Windows\System32\svchost.exe -k LocalServiceNetworkRestricted"
        },
        {
            "Name": "DefiantService",
            "DisplayName": "Defiant Security Service",
            "BinPath": r'"C:\Program Files\Defiant\defiant.exe"'
        }
    ]
    findings = assess_services(services)
    assert len(findings) == 0


def test_services_module_findings():
    services = [
        {
            "Name": "VulnerableSvc",
            "DisplayName": "Unquoted Path Service",
            "BinPath": r"C:\Program Files\Common Files\My Svc\service.exe -run"
        },
        {
            "Name": "SuspiciousSvc",
            "DisplayName": "Service in Temp Directory",
            "BinPath": r"C:\Users\Public\AppData\Local\Temp\malicious.exe"
        }
    ]
    findings = assess_services(services)
    finding_ids = {f["id"] for f in findings}
    assert "SVC-001" in finding_ids
    assert "SVC-002" in finding_ids


# ==============================================================================
# 7. PORTS MODULE
# ==============================================================================

def test_ports_module_compliant():
    listening_ports = [
        {"Port": 8080, "LocalAddress": "127.0.0.1", "ProcessName": "node.exe"},
        {"Port": 5000, "LocalAddress": "127.0.0.1", "ProcessName": "python.exe"}
    ]
    with patch("psutil.net_connections", return_value=[]):
        findings = assess_ports(listening_ports)
    assert len(findings) == 0


def test_ports_module_exposed_risks():
    listening_ports = [
        {"Port": 3389, "LocalAddress": "0.0.0.0", "ProcessName": "svchost.exe"},
        {"Port": 445, "LocalAddress": "::", "ProcessName": "System"},
        {"Port": 23, "LocalAddress": "0.0.0.0", "ProcessName": "telnetd.exe"}
    ]
    with patch("psutil.net_connections", return_value=[]):
        findings = assess_ports(listening_ports)
    finding_ids = {f["id"] for f in findings}
    assert "NET-001" in finding_ids
    assert "NET-002" in finding_ids
    assert "NET-003" in finding_ids


# ==============================================================================
# 8. STARTUP MODULE
# ==============================================================================

def test_startup_module_assessment():
    clean_items = [
        {"Name": "OneDrive", "Command": r'"C:\Program Files\Microsoft OneDrive\OneDrive.exe" /background', "Location": "HKCU"}
    ]
    assert len(assess_startup(clean_items)) == 0

    suspicious_items = [
        {"Name": "TempApp", "Command": r"C:\Users\Default\Downloads\installer.exe", "Location": "HKLM"},
        {"Name": "ScriptPersist", "Command": r"powershell.exe -windowstyle hidden -enc AAAA", "Location": "Startup Folder"}
    ]
    findings = assess_startup(suspicious_items)
    finding_ids = {f["id"] for f in findings}
    assert "STARTUP-001" in finding_ids
    assert "STARTUP-002" in finding_ids


# ==============================================================================
# 9. UPDATES MODULE
# ==============================================================================

def test_updates_module_assessment():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    recent_updates = [{"HotFixID": "KB5034441", "InstalledOn": today}]
    assert len(assess_updates(recent_updates)) == 0

    no_updates = []
    f_none = assess_updates(no_updates)
    assert any(f["id"] == "UPD-002" for f in f_none)

    old_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    old_updates = [{"HotFixID": "KB5000000", "InstalledOn": old_date}]
    f_old = assess_updates(old_updates)
    assert any(f["id"] == "UPD-003" for f in f_old)


# ==============================================================================
# 10. EVENT LOGS MODULE
# ==============================================================================

def test_event_logs_module_assessment():
    clean_stats = {"FailedLogons": 2, "ClearedLogs": 0, "NewAccounts": 0}
    assert len(assess_event_logs(clean_stats)) == 0

    risky_stats = {"FailedLogons": 45, "ClearedLogs": 1, "NewAccounts": 2}
    findings = assess_event_logs(risky_stats)
    finding_ids = {f["id"] for f in findings}
    assert "EVT-001" in finding_ids
    assert "EVT-002" in finding_ids
    assert "EVT-003" in finding_ids


# ==============================================================================
# 11. FIM MODULE
# ==============================================================================

def test_fim_module_lifecycle(in_memory_db, monkeypatch, tmp_path):
    test_file = tmp_path / "critical_file.txt"
    test_file.write_text("initial secure content", encoding="utf-8")
    test_path = str(test_file)

    monkeypatch.setattr("modules.fim.CRITICAL_FILES", [test_path])

    # First run establishes baseline (records FIM-INFO)
    findings_1 = audit_fim()
    assert len(findings_1) == 1
    assert findings_1[0]["id"] == "FIM-INFO"

    # Second run without changes passes with zero findings
    findings_2 = audit_fim()
    assert len(findings_2) == 0

    # Modify file to trigger FIM alert (FIM-001)
    test_file.write_text("tampered malicious content", encoding="utf-8")
    findings_3 = audit_fim()
    assert len(findings_3) == 1
    assert findings_3[0]["id"] == "FIM-001"
    assert "File Integrity Violation" in findings_3[0]["title"]


# ==============================================================================
# 12. DRIVERS MODULE
# ==============================================================================

def test_drivers_module_assessment():
    clean_drivers = [
        {"Name": "Null", "PathName": r"C:\Windows\System32\drivers\null.sys", "State": "Running"}
    ]
    assert len(assess_drivers(clean_drivers)) == 0

    vulnerable_drivers = [
        {"Name": "RTCore64", "PathName": r"C:\Windows\System32\drivers\RTCore64.sys", "State": "Running"},
        {"Name": "Capcom", "PathName": r"C:\Temp\capcom.sys", "State": "Stopped"}
    ]
    findings = assess_drivers(vulnerable_drivers)
    assert len(findings) == 2
    assert all(f["id"] == "DRV-001" for f in findings)


# ==============================================================================
# 13. REGISTRY MODULE
# ==============================================================================

def test_registry_module_assessment():
    clean_registry = [
        {"Name": "UAC_EnableLUA", "Value": 1},
        {"Name": "LMCompatibilityLevel", "Value": 5},
        {"Name": "DisableAntiSpyware", "Value": 0},
        {"Name": "RequireSecuritySignature", "Value": 1}
    ]
    assert len(assess_registry(clean_registry)) == 0

    vulnerable_registry = [
        {"Name": "UAC_EnableLUA", "Value": 0},
        {"Name": "LMCompatibilityLevel", "Value": 1},
        {"Name": "DisableAntiSpyware", "Value": 1},
        {"Name": "RequireSecuritySignature", "Value": 0}
    ]
    findings = assess_registry(vulnerable_registry)
    finding_ids = {f["id"] for f in findings}
    assert "REG-001" in finding_ids
    assert "REG-002" in finding_ids
    assert "REG-003" in finding_ids
    assert "REG-004" in finding_ids


# ==============================================================================
# 14. ML ANOMALY MODULE
# ==============================================================================

def test_ml_anomaly_module(in_memory_db, monkeypatch):
    import numpy as np
    monkeypatch.setattr("modules.ml_anomaly.ML_AVAILABLE", True)

    baseline = generate_training_baseline()
    assert isinstance(baseline, np.ndarray)
    assert baseline.ndim == 2

    with patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 40.0
        findings = audit_anomalies()
        assert isinstance(findings, list)


# ==============================================================================
# 15. THREAT INTEL MODULE
# ==============================================================================

def test_threat_intel_module():
    with patch.dict(os.environ, {"FALCON_CLIENT_ID": "", "FALCON_CLIENT_SECRET": ""}):
        iocs = fetch_crowdstrike_iocs()
        assert "bad_hashes" in iocs
        assert "bad_ips" in iocs
        assert len(iocs["bad_hashes"]) >= 2

    findings = scan_threat_intel()
    assert isinstance(findings, list)


# ==============================================================================
# 16. COMPLIANCE & REPORTING MODULES
# ==============================================================================

def test_compliance_report_generation():
    all_findings = [
        {"id": "REG-001", "description": "UAC Disabled", "recommendation": "Enable UAC"},
        {"id": "FIM-001", "description": "Modified hosts file", "recommendation": "Revert file"}
    ]
    report = generate_compliance_report(all_findings)
    for fw in ["CIS", "NIST", "STIG", "ISO 27001", "HIPAA", "PCI"]:
        assert fw in report
        assert "passed" in report[fw]
        assert "failed" in report[fw]
        assert "compliance_score" in report[fw]
        assert 0.0 <= report[fw]["compliance_score"] <= 100.0


def test_system_info_collection():
    info = get_system_info()
    assert "Computer Name" in info
    assert "Operating System" in info
    assert "RAM (GB)" in info
    assert "CPU Cores" in info


def test_report_generation(tmp_path):
    score_data = {
        "total_earned": 180,
        "total_possible": 190,
        "percentage": 94.7,
        "category_scores": {"Defender": 10, "Firewall": 10}
    }
    findings = [{"id": "DEF-001", "title": "Defender Disabled", "severity": "HIGH"}]

    # Test JSON report
    json_path = generate_json_report(score_data, findings, output_dir=str(tmp_path))
    assert os.path.exists(json_path)
    with open(json_path, "r") as f:
        loaded = json.load(f)
        assert loaded["score_summary"]["total_earned"] == 180

    # Test HTML report
    html_path = generate_html_report(score_data, findings, category_weights={}, output_dir=str(tmp_path))
    if html_path:
        assert os.path.exists(html_path)
