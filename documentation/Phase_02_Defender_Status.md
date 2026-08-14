# Phase 2: Windows Defender Status & Endpoint Protection

## 2.1 Academic Overview & Motivation
Endpoint Protection Platforms (EPP) and Next-Generation Antivirus (NGAV) are the primary bulwarks against malware execution. In modern Windows environments, Microsoft Defender is deeply integrated into the OS kernel via ELAM (Early Launch Anti-Malware). Phase 2 evaluates whether the local user or a malicious actor has tampered with or disabled this critical security boundary.

This phase enforces **CIS Control 10: Malware Defenses**, which requires the continuous monitoring and updating of anti-malware software across all enterprise assets.

## 2.2 Technical Objectives
1. **Verify Real-Time Protection:** Ensure that the file system filter driver is actively intercepting and scanning file reads/writes.
2. **Verify Heuristics (Behavior Monitoring):** Traditional signature-based AV is obsolete against zero-day threats. Behavior monitoring must be active to detect ransomware encryption patterns.
3. **Evaluate Signature Age:** Determine if the endpoint is successfully communicating with Microsoft Update servers to receive new threat definitions.

## 2.3 Algorithmic Implementation & Libraries
Unlike WMI (Windows Management Instrumentation), which often contains outdated classes for antivirus status (`AntiVirusProduct` in `SecurityCenter2`), the modern approach requires interacting with the `MpCmdRun` or Defender PowerShell modules.

The platform executes a highly specific PowerShell cmdlet:
`Get-MpComputerStatus | Select-Object -Property AntivirusEnabled, AMServiceEnabled, RealTimeProtectionEnabled, BehaviorMonitorEnabled, AntispywareSignatureAge | ConvertTo-Json`

### Why ConvertTo-Json?
PowerShell traditionally outputs text streams formatted for human readability. By piping the object into `ConvertTo-Json`, the Python `subprocess` module can capture `stdout` and instantly deserialize it using `json.loads()`. This completely eliminates the need for fragile regex parsing of terminal outputs.

### Core Execution Block
```python
import subprocess, json

def get_defender_status():
    cmd = ["powershell", "-Command", "Get-MpComputerStatus | ConvertTo-Json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None # Graceful degradation if Defender is entirely removed
```

## 2.4 Vulnerability Assessment Logic
The `assess_defender()` function applies deterministic boolean logic to the JSON payload. The severity levels map loosely to CVSS (Common Vulnerability Scoring System) impact metrics.

| Finding ID | Trigger Condition | Severity | Justification |
| :--- | :--- | :--- | :--- |
| **DEF-001** | `AntivirusEnabled == False` | **CRITICAL** | Core AV engine is disabled. Endpoint is naked. |
| **DEF-002** | `RealTimeProtectionEnabled == False` | **CRITICAL** | File execution is permitted without inline scanning. |
| **DEF-003** | `BehaviorMonitorEnabled == False` | **HIGH** | Vulnerable to obfuscated or zero-day ransomware. |
| **DEF-004** | `AntispywareSignatureAge > 7` | **MEDIUM** | Stale definitions limit detection of known, recent malware hashes. |

## 2.5 Architectural Impact (Scoring)
Defender status is one of the two most heavily weighted categories in the Defiant platform (Max: 20 points). A single `CRITICAL` finding here deducts 10 points. If both Real-Time Protection and the AV engine are disabled, the category score is floored at 0, severely impacting the overall system health percentage.
