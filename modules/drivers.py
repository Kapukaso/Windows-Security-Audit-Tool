from utils.powershell import run_powershell_json

def get_drivers():
    cmd = "Get-CimInstance Win32_SystemDriver | Select-Object Name, PathName, State | ConvertTo-Json -Depth 2"
    result = run_powershell_json(cmd)
    if isinstance(result, dict) and "error" in result:
        return []
    if isinstance(result, dict):
        result = [result]
    return result

def assess_drivers(drivers):
    findings = []
    # Simplified blocklist of known BYOVD drivers
    blocklist = ["capcom.sys", "gdrv.sys", "RTCore64.sys", "ATSZIO64.sys", "rzpnk.sys"]
    
    import os
    for d in drivers:
        path = str(d.get("PathName", ""))
        # Extract exact filename to prevent false positives (e.g. gdrv.sys vs ehstortcgdrv.sys)
        filename = os.path.basename(path.replace('\\', '/')).lower()
        
        if filename in [b.lower() for b in blocklist]:
            findings.append({
                "id": "DRV-001",
                "category": "Drivers",
                "severity": "CRITICAL",
                "title": f"Vulnerable Kernel Driver Detected ({d.get('Name')})",
                "description": f"The driver {path} is heavily abused by malware for privilege escalation (BYOVD attacks).",
                "mitre": "T1068 (Exploitation for Privilege Escalation)",
                "recommendation": "Remove or disable this vulnerable driver immediately."
            })
    return findings

def display_drivers(drivers, findings):
    print("\n--- Kernel Driver Findings ---")
    if not findings:
        print("No vulnerable drivers detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")