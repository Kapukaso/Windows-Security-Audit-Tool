"""
modules/startup.py

Collects and analyzes Windows startup applications.
"""
from tabulate import tabulate
from utils.powershell import run_powershell_json

def assess_startup(startup_items):
    """
    Analyzes startup items for suspicious commands or locations.
    """
    findings = []
    
    for item in startup_items:
        name = item.get("Name", "Unknown")
        command = str(item.get("Command", "")).lower()
        location = item.get("Location", "Unknown")
        
        # Check 1: Suspicious execution locations (Temp, Downloads)
        suspicious_paths = ["\\temp\\", "\\downloads\\", "\\appdata\\local\\temp\\"]
        if any(susp_path in command for susp_path in suspicious_paths):
            findings.append({
                "id": "STARTUP-001",
                "title": "Startup Item in Suspicious Location",
                "category": "Startup",
                "severity": "HIGH",
                "description": f"Startup item '{name}' runs from a potentially unsafe location: {command}",
                "recommendation": "Investigate if this is a legitimate application or malware persistence."
            })
            
        # Check 2: Script interpreters in startup
        # Attackers often place PowerShell, CMD, or VBScript commands in startup to download payloads or run memory-only malware
        script_interpreters = ["powershell.exe", "cmd.exe", "cscript.exe", "wscript.exe", "mshta.exe"]
        if any(interpreter in command for interpreter in script_interpreters):
            findings.append({
                "id": "STARTUP-002",
                "title": "Script Interpreter in Startup",
                "category": "Startup",
                "severity": "MEDIUM",
                "description": f"Startup item '{name}' executes a script interpreter: {command}",
                "recommendation": "Verify the script being executed is authorized and not malicious."
            })
            
    return findings


def get_startup_apps():
    """
    Retrieves startup items using WMI via PowerShell.
    """
    # Win32_StartupCommand elegantly pulls from HKLM/HKCU Run keys as well as the Startup folders.
    command = r"""
    Get-CimInstance Win32_StartupCommand | 
    Select-Object Name, Command, Location, User | 
    ConvertTo-Json -Depth 2
    """
    
    result = run_powershell_json(command)
    
    if isinstance(result, dict) and "error" in result:
        return result
        
    # Convert single item to list if only one startup item exists
    if isinstance(result, dict):
        result = [result]
        
    cleaned_startup = []
    
    if not result:
        return cleaned_startup

    for item in result:
        if not item.get("Command"):
            continue
            
        cleaned_startup.append({
            "Name": item.get("Name", "Unknown"),
            "Command": item.get("Command", "Unknown"),
            "Location": item.get("Location", "Unknown"),
            "User": item.get("User", "Unknown")
        })
        
    return cleaned_startup


def display_startup(startup_items, findings):
    """
    Display startup items and security findings.
    """
    if isinstance(startup_items, dict) and "error" in startup_items:
        print(f"Error: {startup_items['error']}")
        return

    table = []
    for item in startup_items:
        # Truncate command for CLI readability
        cmd = item["Command"]
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
            
        table.append([
            item["Name"],
            cmd,
            item["Location"]
        ])

    print("\n--- Startup Applications ---")
    print(
        tabulate(
            table,
            headers=["Name", "Command", "Location/Registry Key"],
            tablefmt="grid"
        )
    )

    print(f"\nTotal Startup Items: {len(startup_items)}")

    print("\n--- Startup Security Findings ---")
    if not findings:
        print("No suspicious startup behavior detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
