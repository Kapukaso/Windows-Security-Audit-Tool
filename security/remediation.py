"""
security/remediation.py
Enterprise Remediation Engine with Preview, Approval, and Rollback support.
"""
from utils.powershell import run_powershell_json
import subprocess
import datetime
from database.database import get_connection, DB_ENGINE

# Define the Remediation Playbooks
PLAYBOOKS = {
    "POL-001": {
        "finding_id": "POL-001",
        "description": "Enforce strict minimum password length (14 characters).",
        "risk_level": "SAFE",
        "preview": "Executes 'net accounts /minpwlen:14' to enforce password length.",
        "execute_cmd": ["net", "accounts", "/minpwlen:14"],
        "rollback_cmd": ["net", "accounts", "/minpwlen:0"],
        "type": "subprocess"
    },
    "POL-002": {
        "finding_id": "POL-002",
        "description": "Enforce account lockout threshold (5 attempts).",
        "risk_level": "SAFE",
        "preview": "Executes 'net accounts /lockoutthreshold:5' to protect against brute-force.",
        "execute_cmd": ["net", "accounts", "/lockoutthreshold:5"],
        "rollback_cmd": ["net", "accounts", "/lockoutthreshold:0"],
        "type": "subprocess"
    },
    "NET-001": {
        "finding_id": "NET-001",
        "description": "Enable Network Level Authentication (NLA) for RDP.",
        "risk_level": "MEDIUM",
        "preview": "Modifies Registry 'UserAuthentication' to 1. May disconnect active legacy RDP sessions.",
        "execute_cmd": r'Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 1',
        "rollback_cmd": r'Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 0',
        "type": "powershell"
    },
    "NET-002": {
        "finding_id": "NET-002",
        "description": "Disable SMBv1 Protocol.",
        "risk_level": "HIGH",
        "preview": "Disables SMBv1 feature. Will break connectivity with legacy network shares/printers. Requires Reboot.",
        "execute_cmd": "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart",
        "rollback_cmd": "Enable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart",
        "type": "powershell"
    },
    "NET-ISOLATE": {
        "finding_id": "NET-ISOLATE",
        "description": "Automated Host Isolation (Block Outbound).",
        "risk_level": "HIGH",
        "preview": "Creates Windows Firewall rule dropping all outbound connections. Will sever remote administration.",
        "execute_cmd": 'New-NetFirewallRule -DisplayName "DEF-ISOLATION" -Direction Outbound -Action Block -Profile Any',
        "rollback_cmd": 'Remove-NetFirewallRule -DisplayName "DEF-ISOLATION"',
        "type": "powershell"
    },
    "DEF-001": {
        "finding_id": "DEF-001",
        "description": "Enable Windows Defender Real-time Protection.",
        "risk_level": "SAFE",
        "preview": "Sets DisableRealtimeMonitoring to $false via MpPreference.",
        "execute_cmd": "Set-MpPreference -DisableRealtimeMonitoring $false",
        "rollback_cmd": "Set-MpPreference -DisableRealtimeMonitoring $true",
        "type": "powershell"
    },
    "FW-001": {
        "finding_id": "FW-001",
        "description": "Enable Windows Firewall across all profiles.",
        "risk_level": "MEDIUM",
        "preview": "Executes 'netsh advfirewall set allprofiles state on'. May block custom applications without explicit rules.",
        "execute_cmd": ["netsh", "advfirewall", "set", "allprofiles", "state", "on"],
        "rollback_cmd": ["netsh", "advfirewall", "set", "allprofiles", "state", "off"],
        "type": "subprocess"
    }
}

def log_remediation_action(finding_id, action_type, status, message):
    """Logs remediation execution or rollback into the database."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ensure table exists
        if DB_ENGINE == "postgres":
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS remediation_log (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                finding_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT
            )
            ''')
            cursor.execute('''
                INSERT INTO remediation_log (timestamp, finding_id, action_type, status, message)
                VALUES (NOW(), %s, %s, %s, %s)
            ''', (finding_id, action_type, status, message))
        else:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS remediation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                finding_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT
            )
            ''')
            cursor.execute('''
                INSERT INTO remediation_log (timestamp, finding_id, action_type, status, message)
                VALUES (datetime('now'), ?, ?, ?, ?)
            ''', (finding_id, action_type, status, message))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log remediation: {e}")

def get_remediation_preview(finding_id):
    """Returns preview metadata for a remediation action."""
    if finding_id not in PLAYBOOKS:
        return {"supported": False, "message": "No automated playbook available for this finding."}
    
    pb = PLAYBOOKS[finding_id]
    return {
        "supported": True,
        "finding_id": pb["finding_id"],
        "description": pb["description"],
        "risk_level": pb["risk_level"],
        "preview": pb["preview"],
        "requires_approval": pb["risk_level"] in ["MEDIUM", "HIGH"]
    }

def _run_action(cmd, cmd_type):
    """Helper to run subprocess or powershell."""
    if cmd_type == "subprocess":
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    else:
        run_powershell_json(cmd)

def execute_remediation(finding_id, approval_granted=False, safe_only_policy=False):
    """Executes the remediation playbook."""
    if finding_id not in PLAYBOOKS:
        return {"success": False, "message": "Automated remediation not supported for this finding."}
        
    pb = PLAYBOOKS[finding_id]
    
    if safe_only_policy and pb["risk_level"] != "SAFE":
        msg = f"Policy Enforcement: Blocked execution. Risk level '{pb['risk_level']}' violates 'Safe Only' policy."
        log_remediation_action(finding_id, "EXECUTE", "BLOCKED", msg)
        return {"success": False, "message": msg}
        
    if pb["risk_level"] in ["MEDIUM", "HIGH"] and not approval_granted:
        msg = f"Execution blocked. Risk level is {pb['risk_level']} and requires explicit approval."
        log_remediation_action(finding_id, "EXECUTE", "BLOCKED", msg)
        return {"success": False, "message": msg, "requires_approval": True}
        
    try:
        _run_action(pb["execute_cmd"], pb["type"])
        msg = "Remediation successfully applied."
        log_remediation_action(finding_id, "EXECUTE", "SUCCESS", msg)
        return {"success": True, "message": msg}
    except Exception as e:
        msg = f"Execution failed: {e}"
        log_remediation_action(finding_id, "EXECUTE", "FAILED", msg)
        return {"success": False, "message": msg}

def rollback_remediation(finding_id):
    """Executes the rollback playbook."""
    if finding_id not in PLAYBOOKS:
        return {"success": False, "message": "No rollback playbook available."}
        
    pb = PLAYBOOKS[finding_id]
    
    try:
        _run_action(pb["rollback_cmd"], pb["type"])
        msg = "Rollback successfully applied. System state restored."
        log_remediation_action(finding_id, "ROLLBACK", "SUCCESS", msg)
        return {"success": True, "message": msg}
    except Exception as e:
        msg = f"Rollback failed: {e}"
        log_remediation_action(finding_id, "ROLLBACK", "FAILED", msg)
        return {"success": False, "message": msg}

def get_remediation_history():
    """Fetches the history of all remediations."""
    try:
        conn = get_connection()
        if DB_ENGINE == "postgres":
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        else:
            conn.row_factory = sqlite3.Row if "sqlite3" in globals() else None
            cursor = conn.cursor()
            
        cursor.execute("SELECT timestamp, finding_id, action_type, status, message FROM remediation_log ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        
        # Format for output
        if DB_ENGINE == "postgres":
            return [dict(r) for r in rows]
        else:
            return [{"timestamp": r[0], "finding_id": r[1], "action_type": r[2], "status": r[3], "message": r[4]} for r in rows]
            
    except Exception:
        return []
