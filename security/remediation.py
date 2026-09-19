"""
security/remediation.py
Provides automated hardening (remediation) actions for specific findings.
"""
from utils.powershell import run_powershell_json
import subprocess

def apply_remediation(finding_id):
    """
    Given a finding ID, executes the safe automated remediation.
    Returns {"success": True/False, "message": "Result string"}
    """
    
    # -------------------------
    # Password Policy
    # -------------------------
    if finding_id == "POL-001":
        try:
            # Set minimum password length to 8
            result = subprocess.run(["net", "accounts", "/minpwlen:8"], check=True, capture_output=True, text=True)
            return {"success": True, "message": "Successfully increased minimum password length to 8."}
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else "Access Denied. Run the server as Administrator."
            return {"success": False, "message": f"Modification blocked: {err_msg}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to modify password policy: {e}"}

    elif finding_id == "POL-002":
        try:
            # Set account lockout threshold to 5
            subprocess.run(["net", "accounts", "/lockoutthreshold:5"], check=True, capture_output=True, text=True)
            return {"success": True, "message": "Successfully set account lockout threshold to 5 attempts."}
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else "Access Denied. Run the server as Administrator."
            return {"success": False, "message": f"Modification blocked: {err_msg}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to modify lockout policy: {e}"}

    # -------------------------
    # Network & Ports
    # -------------------------
    elif finding_id == "NET-001":
        try:
            # Set NLA via Registry key
            cmd = r'Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -Value 1'
            run_powershell_json(cmd)
            return {"success": True, "message": "Successfully enabled Network Level Authentication for RDP."}
        except Exception as e:
            return {"success": False, "message": f"Failed to enable NLA: {e}"}

    elif finding_id == "NET-002":
        try:
            # Disable SMBv1 feature
            cmd = "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart"
            result = run_powershell_json(cmd)
            return {"success": True, "message": "Initiated SMBv1 disabling. (May require a system restart)."}
        except Exception as e:
            return {"success": False, "message": f"Failed to disable SMB: {e}"}
            
    # -------------------------
    # Defender & Firewall
    # -------------------------
    elif finding_id == "DEF-001":
        try:
            cmd = "Set-MpPreference -DisableRealtimeMonitoring $false"
            run_powershell_json(cmd)
            return {"success": True, "message": "Successfully enabled Windows Defender Real-time Protection."}
        except Exception as e:
            return {"success": False, "message": f"Failed to enable Defender: {e}"}

    elif finding_id == "FW-001":
        try:
            cmd = "netsh advfirewall set allprofiles state on"
            subprocess.run(cmd.split(), check=True, capture_output=True, text=True)
            return {"success": True, "message": "Successfully enabled all Windows Firewall profiles."}
        except Exception as e:
            return {"success": False, "message": f"Failed to enable Firewall: {e}"}

    # -------------------------
    # Event Logs & Updates
    # -------------------------
    elif finding_id == "EVT-001":
        try:
            # Set account lockout threshold to 5
            subprocess.run(["net", "accounts", "/lockoutthreshold:5"], check=True, capture_output=True, text=True)
            return {"success": True, "message": "Set account lockout threshold to 5 attempts due to brute force risk."}
        except Exception as e:
            return {"success": False, "message": f"Failed to modify lockout policy: {e}"}

    elif finding_id == "UPD-001":
        try:
            subprocess.run(["wuauclt", "/detectnow"], check=True, capture_output=True, text=True)
            return {"success": True, "message": "Initiated Windows Update check."}
        except Exception as e:
            return {"success": False, "message": f"Failed to initiate Windows Update: {e}"}

    # -------------------------
    # Services (Example)
    # -------------------------
    elif finding_id == "SVC-001":
        return {"success": False, "message": "Unquoted service paths require manual Registry editing to prevent breaking the application."}

    # -------------------------
    # Default Fallback
    # -------------------------
    else:
        return {"success": False, "message": f"Automated remediation is not yet supported or safe for finding {finding_id}."}
