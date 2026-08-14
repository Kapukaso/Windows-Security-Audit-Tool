"""
modules/event_logs.py

Analyzes Windows Event Logs for security-relevant patterns.
"""
from tabulate import tabulate
from utils.powershell import run_powershell_json

def assess_event_logs(log_stats):
    """
    Analyzes event log statistics for security anomalies.
    """
    findings = []
    
    if isinstance(log_stats, dict) and "error" in log_stats:
        # Access denied is expected if not running as admin
        return findings

    failed_logons = log_stats.get("FailedLogons", 0)
    cleared_logs = log_stats.get("ClearedLogs", 0)
    new_services = log_stats.get("NewServices", 0)
    new_accounts = log_stats.get("NewAccounts", 0)
    
    # Check 1: Brute-force / Password guessing detection
    if failed_logons > 50:
        findings.append({
            "id": "EVT-001",
            "title": "High Volume of Failed Logons",
            "category": "Event Logs",
            "severity": "HIGH",
            "description": f"Detected {failed_logons} failed logon attempts (Event ID 4625) in the last 7 days.",
            "recommendation": "Investigate potential brute-force attacks and ensure account lockout policies are enforced."
        })
        
    # Check 2: Audit log clearing (Defense Evasion)
    if cleared_logs > 0:
        findings.append({
            "id": "EVT-002",
            "title": "Security Event Log Cleared",
            "category": "Event Logs",
            "severity": "CRITICAL",
            "description": f"The Security Event Log was cleared {cleared_logs} times recently (Event ID 1102).",
            "recommendation": "Investigate immediately. Clearing security logs is a common technique used by attackers to hide their tracks."
        })
        
    # Check 3: New account creation
    if new_accounts > 0:
        findings.append({
            "id": "EVT-003",
            "title": "New User Accounts Created",
            "category": "Event Logs",
            "severity": "LOW",
            "description": f"{new_accounts} new user accounts were created (Event ID 4720).",
            "recommendation": "Verify that these account creations were authorized."
        })
        
    return findings


def get_event_log_stats():
    """
    Retrieves counts of critical security events from the last 7 days.
    """
    command = r"""
    # Check for Admin privileges first (Security log requires it)
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        @{ error = "Access Denied. Viewing the Security Event Log requires Administrator privileges." } | ConvertTo-Json
        exit
    }
    
    $cutoff = (Get-Date).AddDays(-7)
    
    # We use Measure-Object to safely count even if the result is null
    $failed = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=$cutoff} -ErrorAction SilentlyContinue | Measure-Object).Count
    $cleared = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=1102; StartTime=$cutoff} -ErrorAction SilentlyContinue | Measure-Object).Count
    $services = (Get-WinEvent -FilterHashtable @{LogName='System'; Id=7045; StartTime=$cutoff} -ErrorAction SilentlyContinue | Measure-Object).Count
    $accounts = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4720; StartTime=$cutoff} -ErrorAction SilentlyContinue | Measure-Object).Count

    @{
        FailedLogons = $failed
        ClearedLogs = $cleared
        NewServices = $services
        NewAccounts = $accounts
    } | ConvertTo-Json
    """
    
    result = run_powershell_json(command)
    return result


def display_event_logs(log_stats, findings):
    """
    Display event log statistics and findings.
    """
    if isinstance(log_stats, dict) and "error" in log_stats:
        print(f"\n--- Event Logs ---\nError: {log_stats['error']}")
        return
        
    table = [
        ["Failed Logons (ID 4625)", log_stats.get("FailedLogons", 0)],
        ["Security Log Cleared (ID 1102)", log_stats.get("ClearedLogs", 0)],
        ["New Services Installed (ID 7045)", log_stats.get("NewServices", 0)],
        ["New Accounts Created (ID 4720)", log_stats.get("NewAccounts", 0)],
    ]
        
    print("\n--- Event Log Statistics (Last 7 Days) ---")
    print(
        tabulate(
            table,
            headers=["Event Type", "Occurrences"],
            tablefmt="grid"
        )
    )
    
    print("\n--- Event Log Security Findings ---")
    if not findings:
        print("No anomalous event patterns detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
