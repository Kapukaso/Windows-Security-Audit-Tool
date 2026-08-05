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
    Evaluates the Defender status and generates findings.

    Args:
        status (dict): Output from get_defender_status()

    Returns:
        list[str]: Security findings
    """

    findings = []

    if "error" in status:
        findings.append(status["error"])
        return findings

    if status.get("AntivirusEnabled"):
        findings.append("✅ Antivirus is enabled")
    else:
        findings.append("❌ Antivirus is disabled")

    if status.get("RealTimeProtectionEnabled"):
        findings.append("✅ Real-time protection is enabled")
    else:
        findings.append("⚠️ Real-time protection is disabled")

    if status.get("BehaviorMonitorEnabled"):
        findings.append("✅ Behavior monitoring is enabled")
    else:
        findings.append("⚠️ Behavior monitoring is disabled")

    if status.get("IoavProtectionEnabled"):
        findings.append("✅ Download protection is enabled")
    else:
        findings.append("⚠️ Download protection is disabled")

    if status.get("NISEnabled"):
        findings.append("✅ Network Inspection System is enabled")
    else:
        findings.append("⚠️ Network Inspection System is disabled")

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