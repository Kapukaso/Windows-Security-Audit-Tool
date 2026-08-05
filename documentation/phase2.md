# Phase 2 — Microsoft Defender Audit

## Goal

Read Microsoft Defender protection settings and translate them into understandable security findings and a score out of 10.

## Files

```text
main.py
modules/
  defender.py
utils/
  powershell.py
```

## Data flow

```text
main.py → get_defender_status() → run_powershell_json() → PowerShell → Microsoft Defender
```

PowerShell runs `Get-MpComputerStatus`, keeps only the required properties, and converts the result to JSON. Python then converts that JSON to a dictionary.

## Defender controls checked

| Property | Meaning |
| --- | --- |
| `AntivirusEnabled` | Antivirus engine is enabled. |
| `RealTimeProtectionEnabled` | Files and processes are scanned in real time. |
| `BehaviorMonitorEnabled` | Suspicious behavior monitoring is active. |
| `IoavProtectionEnabled` | Download and attachment protection is active. |
| `NISEnabled` | Network Inspection System is enabled. |

## Functions

- `get_defender_status()` retrieves the status dictionary. It must always `return status` after calling `run_powershell_json()`.
- `assess_defender(status)` turns the data into user-facing findings.
- `defender_score(status)` awards two points for each enabled control, up to 10.
- `run_powershell_json(command)` centralizes PowerShell execution and JSON parsing.

## Error handling

If PowerShell cannot execute or JSON cannot be parsed, the utility returns an `error` dictionary instead of crashing. The Defender module displays the error as a finding and returns a score of zero.

## Verification

Run:

```powershell
python main.py
```

Expected output includes a Microsoft Defender table, five findings, and a `Defender Security Score: x/10` line. On systems where Defender is managed by another antivirus product, some controls may be false or unavailable; report the actual result rather than changing the system.

