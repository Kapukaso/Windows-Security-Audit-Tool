# Developer Guide

This guide explains how to extend and maintain the Defiant Windows Security Posture Platform. The platform uses a modular, decoupled architecture where data collection, risk assessment, compliance mapping, database persistence, and automated remediation can be developed and tested independently.

---

## 1. Directory Structure

```text
app.py                  Flask server, REST API endpoints, and authentication middleware
main.py                 Audit orchestration, ThreadPoolExecutor, and score aggregation
database/
  database.py           Dual-engine persistence (SQLite / PostgreSQL), schema migrations, TTL pruning
modules/
  compliance.py         Multi-standard compliance mapping (CIS, NIST, ISO 27001, HIPAA)
  cve_lookup.py         NIST NVD lookup with persistent caching and circuit breaker
  defender.py           Microsoft Defender status and signature freshness
  drivers.py            Vulnerable and malicious driver blocklist detection
  event_logs.py         Bounded 24-hour Windows Event Log anomaly collection
  fim.py                File Integrity Monitoring with SHA-256 baselines
  firewall.py           Windows Firewall profile evaluation
  ml_anomaly.py         Isolation Forest machine learning telemetry anomaly detection
  password_policy.py    Local account security, lockout thresholds, and NTLMv2
  ports.py              Listening port enumeration and exposed service detection
  registry.py           Deep kernel & registry hardening (LSA, Credential Guard, UAC)
  report.py             HTML and JSON report compilation
  score.py              Mathematical risk deduction model across 13 categories
  services.py           Service configuration and unquoted service path detection
  software.py           Installed software inventory collection and sanitization
  startup.py            Startup applications and persistence audit
  system.py             Host identity and basic hardware specs collection
  threat_intel.py       CrowdStrike Falcon API & offline IOC matching
  updates.py            Windows Update patch state assessment
  users.py              Local users and administrator group audit
security/
  remediation.py        Declarative remediation playbooks, preview, execution, and rollback
  verification.py       WinVerifyTrust Authenticode signature verification and LRU cache
templates/
  dashboard.html        Single-port Sci-Fi HUD dashboard (Tailwind CSS, Lucide Icons)
  report.html           Standalone audit report template
tests/
  conftest.py           Hermetic Pytest fixtures for WMI, PowerShell, and WinTrust ctypes
  test_api.py           Flask REST API route and authentication tests
  test_audit.py         Risk scoring math tests
  test_audit_modules.py Unit and mock tests for all 16 collectors
  test_database.py      Database schema, indexing, and dual-engine parity tests
  test_remediation.py   Remediation playbook preview, approval, and rollback tests
```

---

## 2. How the Audit Loop Works

When `run_full_audit()` is called in `main.py` (or triggered via `POST /api/scan`):
1. **Parallel Collection**: All 16 collection functions in `modules/` are submitted to a `ThreadPoolExecutor(max_workers=10)` for concurrent execution.
2. **Assessment & Findings**: As raw data is collected, assessment functions (`assess_*`) evaluate configurations against security baselines and return structured finding objects:
   ```python
   {
       "id": "REG-001",
       "category": "Registry & Drivers",
       "severity": "HIGH",
       "title": "LSA RunAsPPL is not enabled",
       "description": "Local Security Authority is running without Protected Process Light.",
       "recommendation": "Enable RunAsPPL in HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa."
   }
   ```
3. **Scoring**: Findings are aggregated into `all_findings` and evaluated by `modules/score.py:calculate_score()`. Each finding deducts points from its category weight (floored at zero), resulting in a weighted score out of 190.
4. **Compliance Mapping**: `modules/compliance.py:generate_compliance_report()` maps findings against CIS Benchmarks, NIST SP 800-53, ISO/IEC 27001, and HIPAA controls.
5. **Persistence**: `database/database.py:save_scan_results()` persists host info, score breakdown, and findings into the configured database (SQLite or PostgreSQL).

---

## 3. Adding a New Security Check

To add a new audit check (e.g., checking for BitLocker disk encryption):

### Step 1: Create the Module
Create `modules/bitlocker.py`. Use standard libraries or `utils/powershell.py:run_powershell_json`:

```python
# modules/bitlocker.py
from utils.powershell import run_powershell_json

def get_bitlocker_status():
    cmd = "Get-BitLockerVolume -MountPoint C: | Select-Object -Property VolumeStatus, ProtectionStatus"
    return run_powershell_json(cmd)

def assess_bitlocker(status):
    findings = []
    if isinstance(status, list) and len(status) > 0:
        vol = status[0]
        if vol.get("ProtectionStatus") != "On":
            findings.append({
                "id": "CRYPTO-001",
                "category": "Data Encryption",
                "severity": "HIGH",
                "title": "BitLocker protection is disabled on C: drive.",
                "description": "System drive is not protected by full-disk BitLocker encryption.",
                "recommendation": "Enable BitLocker encryption using manage-bde or the Control Panel."
            })
    return findings
```

### Step 2: Register in `main.py`
Add the collector task to `tasks` dictionary and aggregate findings:

```python
from modules.bitlocker import get_bitlocker_status, assess_bitlocker

# Inside run_full_audit():
tasks["bitlocker"] = get_bitlocker_status

# In findings processing:
bitlocker_status = results.get("bitlocker")
bitlocker_findings = assess_bitlocker(bitlocker_status)
all_findings.extend(bitlocker_findings)
```

### Step 3: Register Weight in `modules/score.py`
Add the category weight to `CATEGORY_WEIGHTS`:
```python
CATEGORY_WEIGHTS = {
    # ...
    "Data Encryption": 15,
}
```

---

## 4. Adding Automated Remediation Playbooks

Remediations in `security/remediation.py` are registered declaratively in the `PLAYBOOKS` dictionary:

```python
PLAYBOOKS["CRYPTO-001"] = {
    "title": "Enable BitLocker Encryption on C: Drive",
    "description": "Initiates XTS-AES 128-bit hardware encryption on the operating system partition.",
    "command": "manage-bde -on C: -UsedSpaceOnly",
    "rollback_cmd": "manage-bde -off C:",
    "safe_only": False,               # Requires explicit admin approval
    "requires_approval": True,
    "impact": "HIGH",
    "verification_fn": lambda: _check_bitlocker_active()
}
```

### Guidelines for "Do No Harm":
1. Always supply a reversible `rollback_cmd`.
2. Set `safe_only: False` and `requires_approval: True` for any action that could affect running applications, open ports, or network connections.
3. Provide a deterministic `verification_fn` that returns `True` only when the underlying state has actually been hardened.

---

## 5. Automated Testing Workflow

All features must include automated tests in the `tests/` directory.

### Running Tests
Execute the Pytest test suite:

```powershell
python -m pytest tests/ -v
```

### Hermetic Mocks (`tests/conftest.py`)
To ensure tests run fast and offline without Administrator privileges, use the provided fixtures:
* `in_memory_db`: Isolates database operations to an in-memory SQLite database.
* `mock_powershell`: Replaces `utils.powershell.run_powershell` and `run_powershell_json` with mocked outputs.
* `mock_wmi`: Replaces WMI queries with synthetic objects.
* `mock_wintrust`: Stubs WinVerifyTrust ctypes calls for process validation.

Example test:
```python
def test_bitlocker_assessment(monkeypatch):
    from modules.bitlocker import assess_bitlocker
    
    mock_data = [{"ProtectionStatus": "Off"}]
    findings = assess_bitlocker(mock_data)
    assert len(findings) == 1
    assert findings[0]["id"] == "CRYPTO-001"
```
