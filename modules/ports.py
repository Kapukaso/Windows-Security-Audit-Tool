"""
modules/ports.py

Collects and analyzes listening network ports.
"""
import psutil
import socket
from tabulate import tabulate

# Common ports and their default services
KNOWN_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    80: "HTTP",
    135: "RPC",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    1433: "MSSQL",
    3306: "MySQL",
    3389: "RDP",
    5900: "VNC",
}

def assess_ports(listening_ports):
    """
    Analyzes listening ports for risky open services.
    """
    findings = []
    
    # Track ports we've already flagged to avoid duplicates (e.g. if IPv4 and IPv6 both listen)
    flagged_ports = set()
    
    for port_info in listening_ports:
        port = port_info.get("Port")
        ip = port_info.get("LocalAddress")
        process_name = port_info.get("ProcessName", "Unknown")
        
        # Only flag if listening on all interfaces (0.0.0.0 or ::)
        # Listening on 127.0.0.1 is local-only and usually fine.
        is_exposed = ip in ("0.0.0.0", "::")
        
        if is_exposed and port not in flagged_ports:
            if port == 3389:
                findings.append({
                    "id": "NET-001",
                    "title": "Remote Desktop Protocol (RDP) Exposed",
                    "category": "Network",
                    "severity": "MEDIUM",
                    "description": f"RDP (Port 3389) is listening on all network interfaces via {process_name}.",
                    "recommendation": "Ensure Network Level Authentication (NLA) is required and restrict access via firewall if possible."
                })
                flagged_ports.add(port)
                
            elif port in (139, 445):
                findings.append({
                    "id": "NET-002",
                    "title": "Windows File Sharing (SMB) Exposed",
                    "category": "Network",
                    "severity": "MEDIUM",
                    "description": f"SMB/NetBIOS (Port {port}) is listening on all network interfaces.",
                    "recommendation": "Ensure SMBv1 is disabled and avoid exposing SMB directly to untrusted networks."
                })
                flagged_ports.add(port)

            elif port in (21, 23):
                findings.append({
                    "id": "NET-003",
                    "title": "Insecure Cleartext Protocol Exposed",
                    "category": "Network",
                    "severity": "HIGH",
                    "description": f"An insecure cleartext protocol (Port {port}) is listening via {process_name}.",
                    "recommendation": "Disable Telnet/FTP and replace with secure alternatives like SSH or SFTP."
                })
                flagged_ports.add(port)
                
    return findings

def get_listening_ports():
    """
    Retrieves all currently listening network ports.
    """
    listening_ports = []
    
    try:
        # psutil net_connections with kind='inet' gives both TCP and UDP
        connections = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        return {"error": "Access Denied. Run as Administrator to view all network connections."}
    except Exception as e:
        return {"error": f"Failed to gather network connections: {e}"}
        
    for conn in connections:
        # For TCP we look for 'LISTEN'. For UDP, there is no state (it's connectionless), so we include all
        if conn.status == 'LISTEN' or conn.type == socket.SOCK_DGRAM:
            pid = conn.pid
            process_name = "Unknown"
            
            if pid:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = "Access Denied / System"

            ip = conn.laddr.ip if conn.laddr else ""
            port = conn.laddr.port if conn.laddr else 0
            protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
            
            if not port:
                continue

            # Identify known service
            service = KNOWN_PORTS.get(port, "Unknown")
            
            listening_ports.append({
                "Protocol": protocol,
                "LocalAddress": ip,
                "Port": port,
                "Service": service,
                "PID": pid,
                "ProcessName": process_name
            })
            
    # Sort by port number
    listening_ports.sort(key=lambda x: x["Port"])
    return listening_ports

def display_ports(ports, findings):
    """
    Display listening network ports and security findings.
    """
    if isinstance(ports, dict) and "error" in ports:
        print(f"Error: {ports['error']}")
        return

    table = []
    for p in ports:
        table.append([
            p["Protocol"],
            f"{p['LocalAddress']}:{p['Port']}",
            p["Service"],
            p["ProcessName"],
            p["PID"]
        ])

    print("\n--- Listening Network Ports ---")
    print(
        tabulate(
            table,
            headers=["Protocol", "Local Address", "Known Service", "Process Name", "PID"],
            tablefmt="grid"
        )
    )

    print(f"\nTotal Listening Ports: {len(ports)}")

    print("\n--- Network Security Findings ---")
    if not findings:
        print("No critical network exposures detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
