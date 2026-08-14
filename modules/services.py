"""
modules/services.py

Collects and audits Windows services.
"""
import psutil
from tabulate import tabulate

def assess_services(services):
    """
    Analyzes services for security misconfigurations like unquoted service paths.
    """
    findings = []
    
    for svc in services:
        binpath = svc.get("BinPath", "")
        username = svc.get("Username", "")
        name = svc.get("Name", "")
        display_name = svc.get("DisplayName", "")
        
        if not binpath or binpath == "Unknown":
            continue

        # Check 1: Unquoted Service Path Vulnerability
        # If the path contains spaces but is not wrapped in quotes, it can be hijacked
        # psutil's binpath includes arguments. We extract the executable part.
        if ".exe" in binpath.lower():
            exe_part = binpath.lower().split(".exe")[0] + ".exe"
            # It's vulnerable if the executable part has a space and isn't quoted
            if " " in exe_part and not exe_part.startswith('"') and not exe_part.startswith("'"):
                findings.append({
                    "id": "SVC-001",
                    "title": "Unquoted Service Path",
                    "category": "Services",
                    "severity": "HIGH",
                    "description": f"Service '{name}' ({display_name}) has an unquoted path with spaces: {exe_part}",
                    "recommendation": "Enclose the service executable path in quotation marks in the Registry (HKLM\\System\\CurrentControlSet\\Services)."
                })

        # Check 2: Service running from User Directory (Suspicious)
        suspicious_paths = ["\\users\\", "\\appdata\\", "\\temp\\", "\\downloads\\"]
        if any(susp_path in binpath.lower() for susp_path in suspicious_paths):
            findings.append({
                "id": "SVC-002",
                "title": "Service in Suspicious Location",
                "category": "Services",
                "severity": "HIGH",
                "description": f"Service '{name}' ({display_name}) is running from a user or temporary directory: {binpath}",
                "recommendation": "Investigate this service for malware or unauthorized persistence."
            })
            
    return findings

def get_services():
    """
    Retrieves a list of Windows services using psutil.
    """
    services_list = []
    
    try:
        for service in psutil.win_service_iter():
            try:
                svc_info = service.as_dict()
                services_list.append({
                    "Name": svc_info.get("name", "Unknown"),
                    "DisplayName": svc_info.get("display_name", "Unknown"),
                    "Status": svc_info.get("status", "Unknown"),
                    "StartType": svc_info.get("start_type", "Unknown"),
                    "Username": svc_info.get("username", "Unknown"),
                    "BinPath": svc_info.get("binpath", "Unknown")
                })
            except psutil.AccessDenied:
                # Skip services we don't have permission to query
                pass
            except Exception:
                pass
    except AttributeError:
        return {"error": "psutil.win_service_iter is not available."}
        
    return services_list

def display_services(services, findings):
    """
    Display a summary of Windows services and related findings.
    """
    if isinstance(services, dict) and "error" in services:
        print(f"Error: {services['error']}")
        return

    # Count statistics
    stats = {}
    for svc in services:
        status = svc.get("Status", "Unknown")
        stats[status] = stats.get(status, 0) + 1

    print("\n--- Services Statistics ---")
    print(f"Total Services: {len(services)}")
    for stat, count in stats.items():
        print(f"- {stat.capitalize()}: {count}")

    print("\n--- Service Security Findings ---")
    if not findings:
        print("No critical service misconfigurations detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")