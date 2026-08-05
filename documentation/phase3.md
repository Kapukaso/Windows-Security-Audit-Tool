# Phase 3 — Windows Firewall Audit

## Goal

Check whether Windows Defender Firewall is enabled for the Domain, Private, and Public network profiles. Each profile protects a different network context; all three should normally be enabled.

## Files to add or update

```text
modules/
  firewall.py       # New Phase 3 module
main.py             # Import and run the module
```

Phase 3 reuses `utils/powershell.py`; do not duplicate PowerShell execution code.

## `modules/firewall.py`

```python
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
```

## Update `main.py`

Add this import below the Defender import:

```python
from modules.firewall import (
    get_firewall_status,
    assess_firewall,
    firewall_score,
)
```

Add this block after the Defender score:

```python
    # --------------------------
    # Phase 3
    # --------------------------
    firewall_status = get_firewall_status()

    print("\n" + "=" * 60)
    print("Windows Firewall")
    print("=" * 60)

    if isinstance(firewall_status, dict) and "error" in firewall_status:
        print(firewall_status["error"])
    else:
        table = [
            [
                profile.get("Name"),
                profile.get("Enabled"),
                profile.get("DefaultInboundAction"),
                profile.get("DefaultOutboundAction"),
            ]
            for profile in firewall_status
        ]
        print(tabulate(
            table,
            headers=["Profile", "Enabled", "Default inbound", "Default outbound"],
            tablefmt="grid",
        ))

    print("\nFirewall Findings\n")
    for finding in assess_firewall(firewall_status):
        print(finding)

    print(f"\nFirewall Security Score: {firewall_score(firewall_status)}/10")
```

## How it works

`Get-NetFirewallProfile` returns the firewall configuration for Domain, Private, and Public networks. The command selects only the fields useful for an audit, then returns JSON. The module normalizes the JSON into a list because PowerShell represents a single result differently from multiple results.

The score is proportional: three enabled profiles score 10/10; two score 7/10; one scores 3/10; none scores 0/10.

## Verification

Run the application from the project root:

```powershell
python main.py
```

You should see a Firewall table followed by three findings. A typical secure result shows Domain, Private, and Public profiles as enabled. This is an audit only; it does not enable, disable, or modify any firewall rule.

## Common issue

If PowerShell reports access restrictions, open the terminal normally first—reading firewall profile settings generally does not require administrator rights. If the device is controlled by an organization, Group Policy may determine the profile configuration; report that result rather than changing it.

