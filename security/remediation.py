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
    elif finding_id == "NET-002":
        try:
            # Disable SMBv1 feature
            cmd = "Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart"
            result = run_powershell_json(cmd)
            return {"success": True, "message": "Initiated SMBv1 disabling. (May require a system restart)."}
        except Exception as e:
            return {"success": False, "message": f"Failed to disable SMB: {e}"}
            
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
