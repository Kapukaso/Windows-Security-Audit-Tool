"""
modules/updates.py

Collects and analyzes Windows Update status and recent hotfixes.
"""
from tabulate import tabulate
from utils.powershell import run_powershell_json
import datetime

def assess_updates(updates):
    """
    Analyzes updates to determine if the system is missing recent security patches.
    """
    findings = []
    
    if isinstance(updates, dict) and "error" in updates:
        findings.append({
            "id": "UPD-001",
            "title": "Unable to Verify Windows Updates",
            "category": "Updates",
            "severity": "MEDIUM",
            "description": "Could not retrieve Windows Update history.",
            "recommendation": "Ensure the Windows Update service is running and accessible."
        })
        return findings

    if not updates:
        findings.append({
            "id": "UPD-002",
            "title": "No Windows Updates Installed",
            "category": "Updates",
            "severity": "CRITICAL",
            "description": "No security updates or hotfixes appear to be installed on this system.",
            "recommendation": "Immediately run Windows Update to secure the system."
        })
        return findings
        
    # Check 1: Age of the most recent update
    latest_date_str = None
    
    for update in updates:
        installed_on = update.get("InstalledOn")
        if installed_on and installed_on != "Unknown":
            # Find the most recent date
            if latest_date_str is None or installed_on > latest_date_str:
                latest_date_str = installed_on
                
    if latest_date_str:
        try:
            # Safely parse the yyyy-mm-dd string
            latest_date = datetime.datetime.strptime(latest_date_str[:10], "%Y-%m-%d")
            days_since_update = (datetime.datetime.now() - latest_date).days
            
            # If the last patch was more than 45 days ago, flag it
            if days_since_update > 45:
                findings.append({
                    "id": "UPD-003",
                    "title": "Outdated Security Patches",
                    "category": "Updates",
                    "severity": "HIGH",
                    "description": f"The last installed update was {days_since_update} days ago ({latest_date_str}).",
                    "recommendation": "Run Windows Update to install the latest security patches."
                })
        except ValueError:
            pass # Unparseable date format
            
    return findings


def get_windows_updates():
    """
    Retrieves the 10 most recently installed hotfixes via PowerShell.
    """
    command = r"""
    Get-HotFix -ErrorAction SilentlyContinue | 
    Select-Object HotFixID, Description, @{Name="InstalledOn";Expression={if ($_.InstalledOn) {$_.InstalledOn.ToString('yyyy-MM-dd')} else {'Unknown'}}} |
    Sort-Object InstalledOn -Descending |
    Select-Object -First 10 | 
    ConvertTo-Json -Depth 2
    """
    
    result = run_powershell_json(command)
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    if isinstance(result, dict):
        result = [result]
        
    if not result:
        return []
        
    cleaned_updates = []
    
    for item in result:
        cleaned_updates.append({
            "HotFixID": item.get("HotFixID", "Unknown"),
            "Description": item.get("Description", "Unknown"),
            "InstalledOn": item.get("InstalledOn", "Unknown")
        })
        
    return cleaned_updates


def display_updates(updates, findings):
    """
    Display recent updates and security findings.
    """
    if isinstance(updates, dict) and "error" in updates:
        print(f"Error: {updates['error']}")
        return
        
    table = []
    for u in updates:
        table.append([
            u.get("HotFixID"),
            u.get("Description"),
            u.get("InstalledOn")
        ])
        
    print("\n--- Recent Windows Updates (Top 10) ---")
    print(
        tabulate(
            table,
            headers=["HotFix ID", "Description", "Install Date"],
            tablefmt="grid"
        )
    )
    
    print("\n--- Update Security Findings ---")
    if not findings:
        print("System appears to be receiving updates recently.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
