"""
Collect and assess local Windows user-account information.
"""

from utils.powershell import run_powershell_json


def get_local_users():
    """Return local users and whether they belong to Administrators."""
    command = """
    $administrators = Get-LocalGroup -SID "S-1-5-32-544"
    $adminSids = Get-LocalGroupMember -Group $administrators |
        ForEach-Object { $_.SID.Value }

    Get-LocalUser |
    Select-Object `
        Name,
        Enabled,
        LastLogon,
        PasswordLastSet,
        PasswordExpires,
        @{Name="IsAdministrator"; Expression={ $adminSids -contains $_.SID.Value }} |
    ConvertTo-Json -Depth 3
    """

    users = run_powershell_json(command)

    if "error" in users:
        return users

    if isinstance(users, dict):
        users = [users]

    return users


def assess_users(users):
    """Create structured dict security findings from local user-account data."""
    if isinstance(users, dict) and "error" in users:
        return [{
            "id": "USR-ERR",
            "category": "Users",
            "severity": "HIGH",
            "title": "User Account Data Unavailable",
            "description": users["error"],
            "recommendation": "Ensure you are running as Administrator."
        }]

    findings = []
    enabled_admins = 0

    for user in users:
        name = user.get("Name", "Unknown")
        enabled = user.get("Enabled", False)
        is_admin = user.get("IsAdministrator", False)

        if name.lower() == "guest" and enabled:
            findings.append({
                "id": "USR-001",
                "category": "Users",
                "severity": "HIGH",
                "title": "Guest Account Enabled",
                "description": "The built-in Guest account is enabled, allowing unauthenticated access.",
                "recommendation": "Disable the Guest account via 'net user guest /active:no'."
            })

        if enabled and is_admin:
            enabled_admins += 1

    if enabled_admins > 2:
        findings.append({
            "id": "USR-002",
            "category": "Users",
            "severity": "MEDIUM",
            "title": f"Excessive Local Administrators ({enabled_admins})",
            "description": f"{enabled_admins} enabled local administrator accounts were found. Attackers who compromise any one of these accounts gain full system access.",
            "recommendation": "Reduce local administrator accounts to the minimum required. Prefer using standard accounts for daily use."
        })

    return findings


def user_score(users):
    """Return a local-account security score out of 10."""
    if isinstance(users, dict) and "error" in users:
        return 0

    score = 10
    enabled_admins = sum(
        user.get("Enabled") and user.get("IsAdministrator")
        for user in users
    )

    guest_enabled = any(
        user.get("Name", "").lower() == "guest" and user.get("Enabled")
        for user in users
    )

    if guest_enabled:
        score -= 4

    if enabled_admins > 2:
        score -= 2

    return max(score, 0)