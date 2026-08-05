from tabulate import tabulate
from modules.system import get_system_info
from modules.defender import (
    get_defender_status,
    assess_defender,
    defender_score
)
from modules.firewall import (
    get_firewall_status,
    assess_firewall,
    firewall_score,
)
from modules.users import (
    get_local_users,
    assess_users,
    user_score,
)

def print_table(title, data):
    """
    Prints a dictionary as a formatted table.
    """

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    table = [[key, value] for key, value in data.items()]

    print(
        tabulate(
            table,
            headers=["Property", "Value"],
            tablefmt="grid"
        )
    )


def main():

    print("=" * 60)
    print("Windows Security Audit Tool")
    print("=" * 60)

    # --------------------------
    # Phase 1
    # --------------------------

    system_info = get_system_info()

    print_table(
        "System Information",
        system_info
    )

    # --------------------------
    # Phase 2
    # --------------------------

    defender_status = get_defender_status()

    print_table(
        "Microsoft Defender",
        defender_status
    )

    print("\nSecurity Findings\n")

    for finding in assess_defender(defender_status):
        print(finding)

    print(
        f"\nDefender Security Score: {defender_score(defender_status)}/10"
    )
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

        # --------------------------
    # Phase 4
    # --------------------------
    users = get_local_users()

    print("\n" + "=" * 60)
    print("Local User Accounts")
    print("=" * 60)

    if isinstance(users, dict) and "error" in users:
        print(users["error"])
    else:
        table = [
            [
                user.get("Name"),
                user.get("Enabled"),
                user.get("IsAdministrator"),
                user.get("PasswordLastSet"),
                user.get("LastLogon"),
            ]
            for user in users
        ]

        print(tabulate(
            table,
            headers=[
                "Username",
                "Enabled",
                "Administrator",
                "Password Last Set",
                "Last Sign-in",
            ],
            tablefmt="grid",
        ))

    print("\nUser Account Findings\n")

    for finding in assess_users(users):
        print(finding)

    print(f"\nUser Account Security Score: {user_score(users)}/10")

if __name__ == "__main__":
    main()