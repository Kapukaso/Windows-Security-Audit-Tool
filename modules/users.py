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
    """Create security findings from local user-account data."""
    if isinstance(users, dict) and "error" in users:
        return [users["error"]]

    findings = []
    enabled_admins = 0

    for user in users:
        name = user.get("Name", "Unknown")
        enabled = user.get("Enabled", False)
        is_admin = user.get("IsAdministrator", False)

        if name.lower() == "guest" and enabled:
            findings.append("❌ The built-in Guest account is enabled")
        elif name.lower() == "guest":
            findings.append("✅ The built-in Guest account is disabled")

        if enabled and is_admin:
            enabled_admins += 1
            findings.append(f"⚠️ {name} is an enabled local administrator")

        if not enabled:
            findings.append(f"ℹ️ {name} is disabled")

    if enabled_admins == 0:
        findings.append("✅ No enabled local administrator accounts were found")
    elif enabled_admins == 1:
        findings.append("✅ One enabled local administrator account was found")
    else:
        findings.append(
            f"⚠️ {enabled_admins} enabled local administrator accounts were found"
        )

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