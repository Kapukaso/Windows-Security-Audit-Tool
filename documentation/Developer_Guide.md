# Developer Guide

This guide explains how to extend the Defiant Windows Security Posture Platform. The platform uses a modular architecture, meaning new security checks can be added independently without rewriting core logic.

## 1. Directory Structure Overview
* **`app.py`**: The Flask web server. Handles routing and API endpoints.
* **`main.py`**: The CLI entry point and core audit loop. It imports all modules and executes them.
* **`modules/`**: Contains the decoupled logic for data collection and assessment.
* **`security/remediation.py`**: Contains the scripts that attempt automated hardening ("Do No Harm" actions).
* **`database/database.py`**: SQLite database schema and I/O.
* **`templates/dashboard.html`**: The UI.
* **`utils/`**: Helper utilities (e.g., executing PowerShell safely).

## 2. How the Audit Loop Works
When `run_full_audit()` is called in `main.py` (or via `/api/scan`):
1. Each Python script in `modules/` is executed concurrently utilizing a `ThreadPoolExecutor` (max 10 workers) for massive performance gains.
2. The scripts typically have a `get_X()` function that collects raw data from Windows, and an `assess_X()` function that analyzes the data.
3. The `assess_X()` function returns a list of "findings" (dictionaries).
4. All findings are collected into a single list `all_findings`.
5. The array is passed to `modules/score.py`, which calculates the deductions.

## 3. Adding a New Security Module
To add a new security check (e.g., checking for BitLocker encryption):

**Step 1: Create the Data Collection Script**
Create `modules/bitlocker.py`. Use standard libraries, `WMI`, or the provided `run_powershell_json` helper to extract the raw data.
```python
# modules/bitlocker.py
from utils.powershell import run_powershell_json

def get_bitlocker_status():
    # Example logic using a PowerShell helper
    cmd = "Get-BitLockerVolume -MountPoint C: | Select-Object -Property VolumeStatus, ProtectionStatus"
    return run_powershell_json(cmd)
```

**Step 2: Create the Assessment Logic**
In the same file, write the logic to analyze the raw data and yield findings.
```python
def assess_bitlocker(status):
    findings = []
    
    # Check if protection is Off
    if isinstance(status, list) and len(status) > 0:
        vol = status[0]
        if vol.get("ProtectionStatus") != "On":
            findings.append({
                "id": "CRYPTO-001",
                "category": "Data Encryption",
                "severity": "HIGH",
                "title": "BitLocker protection is currently disabled on the C: drive."
            })
    return findings
```

**Step 3: Register the Module in the Core Loop**
Open `main.py`. Import your new module and add its collection function to the concurrent `tasks` dictionary, and process its findings.
```python
from modules.bitlocker import get_bitlocker_status, assess_bitlocker

def run_full_audit(progress_tracker=None):
    # ... existing code ...
    
    tasks = {
        "system_info": get_system_info,
        "defender": get_defender_status,
        # ... Add your task here ...
        "bitlocker": get_bitlocker_status
    }
    
    # ... further down, after ThreadPoolExecutor completes ...
    
    bitlocker_status = results.get("bitlocker")
    bitlocker_findings = assess_bitlocker(bitlocker_status)
    all_findings.extend(bitlocker_findings)
    
    # ... rest of code ...
```

**Step 4: Update the Scoring Model (Optional)**
If you are adding a completely new category, open `modules/score.py` and add it to `CATEGORY_WEIGHTS`:
```python
CATEGORY_WEIGHTS = {
    # ... existing categories ...
    "Data Encryption": 15,
}
```

## 4. Adding Automated Remediation
To allow users to automatically fix a vulnerability from the dashboard:

1. Open `security/remediation.py`.
2. Locate the `apply_remediation(finding_id)` function.
3. Add a new `elif` branch matching the ID of your new finding:

```python
elif finding_id == "CRYPTO-001":
    try:
        # Warning: Ensure the command is safe to run automatically!
        subprocess.run(["manage-bde", "-on", "C:"], check=True, capture_output=True)
        return {"success": True, "message": "Initiated BitLocker encryption on C: drive."}
    except Exception as e:
        return {"success": False, "message": f"Failed to enable BitLocker: {e}"}
```

*Note on "Do No Harm":* Never build automated remediations that delete user files, arbitrarily kill processes, or make complex irreversible registry changes. If it's complex or dangerous, flag it in the UI and let a human system administrator handle it.
