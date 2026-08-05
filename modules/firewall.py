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
    """Return findings for each firewall profile."""
    if isinstance(status, dict) and "error" in status:
        return [status["error"]]

    findings = []
    for profile in status:
        name = profile.get("Name", "Unknown")
        if profile.get("Enabled"):
            findings.append(f"✅ {name} firewall profile is enabled")
        else:
            findings.append(f"❌ {name} firewall profile is disabled")

    return findings


def firewall_score(status):
    """Return a score out of 10 based on enabled firewall profiles."""
    if isinstance(status, dict) and "error" in status:
        return 0

    enabled_profiles = sum(profile.get("Enabled") is True for profile in status)
    return round((enabled_profiles / 3) * 10)