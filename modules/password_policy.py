"""
modules/password_policy.py

Collects and analyzes the local password and account lockout policy.
"""
import subprocess
from tabulate import tabulate

def get_password_policy():
    """
    Retrieves the local password policy using the built-in 'net accounts' command.
    """
    policy = {}
    
    try:
        # Run net accounts, capture output securely without shell=True
        result = subprocess.run(["net", "accounts"], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                policy[key.strip()] = value.strip()
                
    except subprocess.CalledProcessError as e:
        return {"error": f"Failed to retrieve password policy. {e}"}
    except Exception as e:
        return {"error": str(e)}
        
    return policy


def assess_password_policy(policy):
    """
    Analyzes password policy against common security baselines (like CIS/NIST).
    """
    findings = []
    
    # We must extract integers safely since values might be strings like 'Never' or 'None'
    def extract_int(val_str):
        try:
            return int(val_str)
        except ValueError:
            return 0
            
    min_length_str = policy.get("Minimum password length", "0")
    max_age_str = policy.get("Maximum password age (days)", "0")
    lockout_str = policy.get("Lockout threshold", "Never")
    
    min_length = extract_int(min_length_str)
    
    # Check 1: Minimum Password Length
    # We use standard guidance. Minimum 8 is an absolute baseline.
    if min_length < 8:
        findings.append({
            "id": "POL-001",
            "title": "Weak Minimum Password Length",
            "category": "Password Policy",
            "severity": "HIGH",
            "description": f"The minimum password length is set to {min_length_str} characters.",
            "recommendation": "Increase the minimum password length to at least 8 (or 14+ for strict environments) to prevent brute-force attacks."
        })
        
    # Check 2: Account Lockout Threshold
    if lockout_str == "Never":
        findings.append({
            "id": "POL-002",
            "title": "Account Lockout Disabled",
            "category": "Password Policy",
            "severity": "HIGH",
            "description": "There is no account lockout threshold configured.",
            "mitre": "T1110 (Brute Force / Weak Lockout Policy)",
            "recommendation": "Set an account lockout threshold (e.g., 5 or 10 invalid attempts) to prevent password guessing attacks."
        })
        
    # Check 3: Maximum Password Age
    # Note: Modern NIST guidance deprecates mandatory rotation without cause, but an infinite
    # setting is still often flagged by legacy compliance frameworks. We mark it as INFO.
    if max_age_str.lower() == "never" or extract_int(max_age_str) > 365:
        findings.append({
            "id": "POL-003",
            "title": "Passwords Configured to Never Expire",
            "category": "Password Policy",
            "severity": "INFO",
            "description": "The maximum password age is extremely high or set to never expire.",
            "mitre": "T1201 (Password Policy Discovery / Weak Policy)",
            "recommendation": "While NIST no longer mandates arbitrary rotation, ensure compensating controls (like MFA) exist."
        })
        
    return findings


def display_password_policy(policy, findings):
    """
    Display the password policy and related findings.
    """
    if "error" in policy:
        print(f"Error: {policy['error']}")
        return
        
    table = []
    for key, val in policy.items():
        if key: # Ignore empty lines/keys
            table.append([key, val])
            
    print("\n--- Password & Account Policy ---")
    print(
        tabulate(
            table,
            headers=["Policy Setting", "Value"],
            tablefmt="grid"
        )
    )
    
    print("\n--- Password Policy Findings ---")
    if not findings:
        print("No significant password policy weaknesses detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
