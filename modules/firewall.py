"""Collect and assess Windows Defender Firewall profile status."""

from utils.powershell import run_powershell_json


def get_firewall_status():
    """Return enabled state for the Windows Firewall network profiles."""
    command = """
    Get-NetFirewallProfile |
    Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
    ConvertTo-Json
    """

    status = run_powershell_json(command)

    if "error" in status:
        return status

    # ConvertTo-Json returns one dictionary for one profile and a list for many.
    if isinstance(status, dict):
        status = [status]

    return status


def assess_firewall(status):
    """Return structured dict findings for each disabled firewall profile."""
    if isinstance(status, dict) and "error" in status:
        return [{
            "id": "FW-ERR",
            "category": "Firewall",
            "severity": "HIGH",
            "title": "Firewall Status Unavailable",
            "description": status["error"],
            "recommendation": "Ensure you are running as Administrator."
        }]

    findings = []
    for profile in status:
        name = profile.get("Name", "Unknown")
        if not profile.get("Enabled"):
            findings.append({
                "id": "FW-001",
                "category": "Firewall",
                "severity": "CRITICAL",
                "title": f"Firewall Profile Disabled: {name}",
                "description": f"The '{name}' Windows Firewall profile is currently disabled.",
                "recommendation": f"Enable the '{name}' firewall profile via Windows Security or 'netsh advfirewall set allprofiles state on'."
            })

    return findings


def firewall_score(status):
    """Return a score out of 10 based on enabled firewall profiles."""
    if isinstance(status, dict) and "error" in status:
        return 0

    # PowerShell returns Enabled as integer 1/0, not Python True/False
    # so we must use bool() rather than 'is True'
    enabled_profiles = sum(bool(profile.get("Enabled")) for profile in status)
    return round((enabled_profiles / 3) * 10)