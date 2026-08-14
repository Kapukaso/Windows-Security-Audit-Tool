from tabulate import tabulate
from modules import software
from modules.system import get_system_info
from modules.software import (
    get_installed_software,
    display_software
)
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
from modules.services import (
    get_services,
    assess_services,
    display_services
)
from modules.startup import (
    get_startup_apps,
    assess_startup,
    display_startup
)
from modules.ports import (
    get_listening_ports,
    assess_ports,
    display_ports
)
from modules.password_policy import (
    get_password_policy,
    assess_password_policy,
    display_password_policy
)
from modules.updates import (
    get_windows_updates,
    assess_updates,
    display_updates
)
from modules.event_logs import (
    get_event_log_stats,
    assess_event_logs,
    display_event_logs
)
from modules.score import (
    calculate_score,
    display_final_score,
    CATEGORY_WEIGHTS
)
from modules.report import (
    generate_json_report,
    generate_html_report
)
from database.database import save_scan_results

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


def run_full_audit():
    """
    Runs all audit modules and returns the raw data, findings, and final score.
    """
    # Phase 1
    system_info = get_system_info()
    
    # Phase 2
    defender_status = get_defender_status()
    defender_findings = assess_defender(defender_status)
    
    # Phase 3
    firewall_status = get_firewall_status()
    firewall_findings = assess_firewall(firewall_status)
    
    # Phase 4
    users = get_local_users()
    user_findings = assess_users(users)
    
    # Phase 5
    software = get_installed_software()
    software_findings = software.get("findings", []) if isinstance(software, dict) else []
    
    # Phase 6
    services = get_services()
    service_findings = assess_services(services)
    
    # Phase 7
    startup_items = get_startup_apps()
    startup_findings = assess_startup(startup_items)
    
    # Phase 8
    ports = get_listening_ports()
    port_findings = assess_ports(ports)
    
    # Phase 9
    policy = get_password_policy()
    policy_findings = assess_password_policy(policy)
    
    # Phase 10
    updates = get_windows_updates()
    update_findings = assess_updates(updates)
    
    # Phase 11
    log_stats = get_event_log_stats()
    log_findings = assess_event_logs(log_stats)

    old_scores = {
        "Defender": defender_score(defender_status),
        "Firewall": firewall_score(firewall_status),
        "Users": user_score(users)
    }

    all_findings = []
    all_findings.extend(defender_findings if isinstance(defender_findings, list) else [])
    all_findings.extend(firewall_findings if isinstance(firewall_findings, list) else [])
    all_findings.extend(user_findings if isinstance(user_findings, list) else [])
    all_findings.extend(software_findings)
    all_findings.extend(service_findings)
    all_findings.extend(startup_findings)
    all_findings.extend(port_findings)
    all_findings.extend(policy_findings)
    all_findings.extend(update_findings)
    all_findings.extend(log_findings)

    score_data = calculate_score(all_findings, old_scores)
    
    return system_info, score_data, all_findings


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

    # --------------------------
    # Phase 4
    # --------------------------

    print("\n" + "=" * 60)
    print("Installed Software")
    print("=" * 60)

    software = get_installed_software()

    display_software(software)

    # --------------------------
    # Phase 5
    # --------------------------

    print("\n" + "=" * 60)
    print("Windows Services")
    print("=" * 60)

    services = get_services()
    service_findings = assess_services(services)
    
    display_services(services, service_findings)

    # --------------------------
    # Phase 6
    # --------------------------

    print("\n" + "=" * 60)
    print("Startup Applications")
    print("=" * 60)

    startup_items = get_startup_apps()
    startup_findings = assess_startup(startup_items)
    
    display_startup(startup_items, startup_findings)

    # --------------------------
    # Phase 7
    # --------------------------

    print("\n" + "=" * 60)
    print("Network & Listening Ports")
    print("=" * 60)

    ports = get_listening_ports()
    port_findings = assess_ports(ports)
    
    display_ports(ports, port_findings)

    # --------------------------
    # Phase 8
    # --------------------------

    print("\n" + "=" * 60)
    print("Password & Account Policy")
    print("=" * 60)

    policy = get_password_policy()
    policy_findings = assess_password_policy(policy)
    
    display_password_policy(policy, policy_findings)

    # --------------------------
    # Phase 9
    # --------------------------

    print("\n" + "=" * 60)
    print("Windows Updates & Hotfixes")
    print("=" * 60)

    updates = get_windows_updates()
    update_findings = assess_updates(updates)
    
    display_updates(updates, update_findings)

    # --------------------------
    # Phase 10
    # --------------------------

    print("\n" + "=" * 60)
    print("Event Log Analysis")
    print("=" * 60)

    log_stats = get_event_log_stats()
    log_findings = assess_event_logs(log_stats)
    
    display_event_logs(log_stats, log_findings)

    # --------------------------
    # Phase 11: Final Scoring
    # --------------------------
    
    # Collect legacy scores (Phases 1-3)
    old_scores = {
        "Defender": defender_score(defender_status),
        "Firewall": firewall_score(firewall_status),
        "Users": user_score(users)
    }

    # Collect dictionary findings (Phases 4-10)
    all_findings = []
    if isinstance(software, dict) and "findings" in software:
        all_findings.extend(software["findings"])
    all_findings.extend(service_findings)
    all_findings.extend(startup_findings)
    all_findings.extend(port_findings)
    all_findings.extend(policy_findings)
    all_findings.extend(update_findings)
    all_findings.extend(log_findings)

    # Calculate and display the score
    score_data = calculate_score(all_findings, old_scores)
    display_final_score(score_data)

    # --------------------------
    # Phase 12: Reporting
    # --------------------------
    
    print("\n" + "=" * 60)
    print("Generating Reports")
    print("=" * 60)

    generate_json_report(score_data, all_findings)
    generate_html_report(score_data, all_findings, CATEGORY_WEIGHTS)

    # --------------------------
    # Phase 13: SQLite History
    # --------------------------
    
    print("\n" + "=" * 60)
    print("Saving to Database")
    print("=" * 60)
    
    scan_id = save_scan_results(system_info, score_data, all_findings)
    print(f"[+] Scan results saved to local SQLite database! (Scan ID: {scan_id})")
    
if __name__ == "__main__":
    main()