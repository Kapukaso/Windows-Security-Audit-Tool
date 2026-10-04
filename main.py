from tabulate import tabulate
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from modules.fim import audit_fim
from modules.ml_anomaly import audit_anomalies
from modules.drivers import get_drivers, assess_drivers
from modules.registry import get_registry_security, assess_registry, display_registry


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


from modules.cve_lookup import audit_software_cves

def run_full_audit(progress_tracker=None):
    """
    Runs all audit modules concurrently and returns the raw data, findings, and final score.
    """
    def update_progress(msg, pct):
        if progress_tracker is not None:
            progress_tracker["message"] = msg
            progress_tracker["percentage"] = pct

    update_progress("Initializing concurrent audit tasks...", 10)

    tasks = {
        "system_info": get_system_info,
        "defender": get_defender_status,
        "firewall": get_firewall_status,
        "users": get_local_users,
        "software": get_installed_software,
        "services": get_services,
        "startup": get_startup_apps,
        "ports": get_listening_ports,
        "policy": get_password_policy,
        "updates": get_windows_updates,
        "logs": get_event_log_stats,
        "fim": audit_fim,
        "ml": audit_anomalies,
        "registry": get_registry_security,
        "drivers": get_drivers
    }

    results = {}
    total_tasks = len(tasks)
    completed_tasks = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
            completed_tasks += 1
            # Base completion up to 70% for standard tasks
            current_pct = 10 + int(60 * (completed_tasks / total_tasks))
            update_progress(f"Completed {futures[future]} scan...", current_pct)

    update_progress("Analyzing raw data for findings...", 75)

    # Process findings
    defender_status = results.get("defender")
    defender_findings = assess_defender(defender_status)

    firewall_status = results.get("firewall")
    firewall_findings = assess_firewall(firewall_status)

    users = results.get("users")
    user_findings = assess_users(users)

    software = results.get("software")
    software_findings = software.get("findings", []) if isinstance(software, dict) else []

    # Run CVE lookup as a synchronous addition after software collection
    update_progress("Checking CVE Database for installed software...", 80)
    software_list = software.get("software", []) if isinstance(software, dict) else []
    cve_findings = audit_software_cves(software_list, progress_tracker)
    software_findings.extend(cve_findings)

    update_progress("Finalizing risk scoring...", 90)

    services = results.get("services")
    service_findings = assess_services(services)

    startup_items = results.get("startup")
    startup_findings = assess_startup(startup_items)

    ports = results.get("ports")
    port_findings = assess_ports(ports)

    policy = results.get("policy")
    policy_findings = assess_password_policy(policy)

    updates = results.get("updates")
    update_findings = assess_updates(updates)

    log_stats = results.get("logs")
    log_findings = assess_event_logs(log_stats)

    fim_findings = results.get("fim")
    ml_findings = results.get("ml")
    
    
    registry_data = results.get("registry")
    registry_findings = assess_registry(registry_data)

    driver_data = results.get("drivers", [])
    driver_findings = assess_drivers(driver_data)


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
    all_findings.extend(fim_findings if isinstance(fim_findings, list) else [])
    all_findings.extend(ml_findings if isinstance(ml_findings, list) else [])
    all_findings.extend(registry_findings if isinstance(registry_findings, list) else [])
    all_findings.extend(driver_findings if isinstance(driver_findings, list) else [])

    score_data = calculate_score(all_findings, old_scores)
    
    raw_data = {
        "defender_status": defender_status,
        "firewall_status": firewall_status,
        "users": users,
        "software": software,
        "services": services,
        "startup_items": startup_items,
        "ports": ports,
        "policy": policy,
        "updates": updates,
        "log_stats": log_stats,
        "registry_data": registry_data
    }
    
    update_progress("Done.", 100)
    
    # Pack the results into the expected tuple format for app.py compatibility, and pass raw data
    return results.get("system_info"), score_data, all_findings, raw_data


def main():

    print("=" * 60)
    print("Windows Security Audit Tool")
    print("=" * 60)

    print("Running asynchronous audit... please wait.")
    system_info, score_data, all_findings, raw_data = run_full_audit()

    # --------------------------
    # Output Phase
    # --------------------------

    print_table(
        "System Information",
        system_info
    )

    print_table(
        "Microsoft Defender",
        raw_data.get("defender_status", {})
    )
    defender_findings = [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Defender"]
    if defender_findings:
        for f in defender_findings:
            print(f"  [{f['severity']}] {f['title']}: {f['description']}")
    else:
        print("  [OK] All Defender protections are enabled.")
    print(f"\nDefender Security Score: {defender_score(raw_data.get('defender_status'))}/10")

    print("\n" + "=" * 60)
    print("Windows Firewall")
    print("=" * 60)
    firewall_status = raw_data.get("firewall_status")
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
            for profile in (firewall_status or [])
        ]
        print(tabulate(
            table,
            headers=["Profile", "Enabled", "Default inbound", "Default outbound"],
            tablefmt="grid",
        ))
    print(f"\nFirewall Security Score: {firewall_score(firewall_status)}/10")

    print("\n" + "=" * 60)
    print("Local User Accounts")
    print("=" * 60)
    users = raw_data.get("users")
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
            for user in (users or [])
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
    print(f"\nUser Account Security Score: {user_score(users)}/10")

    print("\n" + "=" * 60)
    print("Installed Software")
    print("=" * 60)
    display_software(raw_data.get("software"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Software"])

    print("\n" + "=" * 60)
    print("Windows Services")
    print("=" * 60)
    display_services(raw_data.get("services"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Services"])

    print("\n" + "=" * 60)
    print("Startup Applications")
    print("=" * 60)
    display_startup(raw_data.get("startup_items"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Startup"])

    print("\n" + "=" * 60)
    print("Network & Listening Ports")
    print("=" * 60)
    display_ports(raw_data.get("ports"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Network"])

    print("\n" + "=" * 60)
    print("Password & Account Policy")
    print("=" * 60)
    display_password_policy(raw_data.get("policy"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Password Policy"])

    print("\n" + "=" * 60)
    print("Windows Updates & Hotfixes")
    print("=" * 60)
    display_updates(raw_data.get("updates"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Updates"])

    print("\n" + "=" * 60)
    print("Event Log Analysis")
    print("=" * 60)
    display_event_logs(raw_data.get("log_stats"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Event Logs"])
    
    print("\n" + "=" * 60)
    print("Registry Security")
    print("=" * 60)
    display_registry(raw_data.get("registry_data"), [f for f in all_findings if isinstance(f, dict) and f.get("category") == "Registry"])

    # --------------------------
    # Final Scoring & Compliance
    # --------------------------
    display_final_score(score_data)
    
    from modules.compliance import generate_compliance_report, display_compliance_report
    compliance_report = generate_compliance_report(all_findings)
    display_compliance_report(compliance_report)

    # --------------------------
    # Reporting
    # --------------------------
    print("\n" + "=" * 60)
    print("Generating Reports")
    print("=" * 60)
    generate_json_report(score_data, all_findings, compliance_report)
    generate_html_report(score_data, all_findings, CATEGORY_WEIGHTS)

    # --------------------------
    # SQLite History
    # --------------------------
    print("\n" + "=" * 60)
    print("Saving to Database")
    print("=" * 60)
    scan_id = save_scan_results(system_info, score_data, all_findings)
    print(f"[+] Scan results saved to local SQLite database! (Scan ID: {scan_id})")
    
if __name__ == "__main__":
    main()