"""
modules/defender.py

This module is responsible for collecting information about
Microsoft Defender Antivirus using PowerShell.

Functions:
    - get_defender_status()
    - assess_defender()
"""

import json

from utils.powershell import run_powershell_json


def get_defender_status():
    """
    Retrieves the current Microsoft Defender status.

    Returns:
        dict:
            {
                "AntivirusEnabled": True,
                "RealTimeProtectionEnabled": True,
                "BehaviorMonitorEnabled": True,
                "IoavProtectionEnabled": True,
                "NISEnabled": True
            }

        OR

        {
            "error": "Unable to retrieve Windows Defender status."
        }
    """

    # PowerShell command
    command = """
    Get-MpComputerStatus |
    Select-Object `
        AntivirusEnabled,
        RealTimeProtectionEnabled,
        BehaviorMonitorEnabled,
        IoavProtectionEnabled,
        NISEnabled |
    ConvertTo-Json
    """

    status = run_powershell_json(command)

    # If PowerShell returned an error, pass it back.
    if "error" in status:
        return status

    # Otherwise return the Defender status.
    return status


def assess_defender(status):
    """
    Evaluates the Defender status and generates structured dict findings.

    Args:
        status (dict): Output from get_defender_status()

    Returns:
        list[dict]: Security findings in standard dict format
    """

    findings = []

    if "error" in status:
        findings.append({
            "id": "DEF-ERR",
            "category": "Defender",
            "severity": "HIGH",
            "title": "Defender Status Unavailable",
            "description": status["error"],
            "recommendation": "Ensure you are running as Administrator."
        })
        return findings

    if not status.get("AntivirusEnabled"):
        findings.append({
            "id": "DEF-001",
            "category": "Defender",
            "severity": "CRITICAL",
            "title": "Antivirus Disabled",
            "description": "Windows Defender Antivirus is not enabled on this system.",
            "mitre": "T1562.001 (Impair Defenses: Disable or Modify Tools)",
            "recommendation": "Enable Windows Defender Antivirus immediately."
        })

    if not status.get("RealTimeProtectionEnabled"):
        findings.append({
            "id": "DEF-002",
            "category": "Defender",
            "severity": "HIGH",
            "title": "Real-Time Protection Disabled",
            "description": "Defender real-time protection is off. Malware can run undetected.",
            "mitre": "T1562.001 (Impair Defenses: Disable or Modify Tools)",
            "recommendation": "Enable Real-Time Protection in Windows Security settings."
        })

    if not status.get("BehaviorMonitorEnabled"):
        findings.append({
            "id": "DEF-003",
            "category": "Defender",
            "severity": "MEDIUM",
            "title": "Behavior Monitoring Disabled",
            "description": "Behavior monitoring is off. Suspicious process activity may go undetected.",
            "mitre": "T1562.001 (Impair Defenses: Disable or Modify Tools)",
            "recommendation": "Enable Behavior Monitoring in Defender settings."
        })

    if not status.get("IoavProtectionEnabled"):
        findings.append({
            "id": "DEF-004",
            "category": "Defender",
            "severity": "MEDIUM",
            "title": "Download Protection Disabled",
            "description": "IOAV (download/attachment scanning) is disabled.",
            "mitre": "T1562.001 (Impair Defenses: Disable or Modify Tools)",
            "recommendation": "Enable cloud-delivered protection and download scanning."
        })

    if not status.get("NISEnabled"):
        findings.append({
            "id": "DEF-005",
            "category": "Defender",
            "severity": "MEDIUM",
            "title": "Network Inspection System Disabled",
            "description": "Defender NIS is not monitoring network traffic for exploit patterns.",
            "mitre": "T1562.001 (Impair Defenses: Disable or Modify Tools)",
            "recommendation": "Enable the Network Inspection System in Defender settings."
        })

    return findings


def defender_score(status):
    """
    Calculates a security score for Microsoft Defender.

    Maximum score: 10

    Returns:
        int
    """

    if "error" in status:
        return 0

    score = 0

    if status.get("AntivirusEnabled"):
        score += 2

    if status.get("RealTimeProtectionEnabled"):
        score += 2

    if status.get("BehaviorMonitorEnabled"):
        score += 2

    if status.get("IoavProtectionEnabled"):
        score += 2

    if status.get("NISEnabled"):
        score += 2

    return score