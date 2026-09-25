# Phase 15: Automated Hardening (Remediation)

## 15.1 Academic Overview
Detection without response is insufficient. Phase 15 introduces SOAR (Security Orchestration, Automation, and Response) capabilities, allowing the dashboard to automatically fix detected misconfigurations.

## 15.2 The "Do No Harm" Principle
Automated remediation is dangerous. If an EDR automatically deletes a critical legacy database driver because it is "outdated," it causes a business outage. 
The Remediation Engine is strictly programmed to only fix **safe configurations** (e.g., Password Policies via `net accounts /minpwlen:8`). Destructive actions (like software uninstallation) are intentionally trapped in a default fallback clause that returns: `"Automated remediation is not yet supported or safe for this finding."`

## 15.3 Implementation
When the user clicks "DEPLOY FIX" on the frontend, a POST request is sent to `/api/remediate` with the `finding_id`. 
The Python engine executes the associated `subprocess` command. It utilizes `try/except subprocess.CalledProcessError` to gracefully catch `Exit Code 2` (Access Denied) exceptions if the Flask server was not launched with Administrator privileges.

## 15.4 Supported Remediations
The platform currently supports safe, automated remediations for the following categories:
- **Password Policy**: Automatically increase minimum password length (`POL-001`) and set account lockout thresholds (`POL-002`, `EVT-001`).
- **Network & Ports**: Enable Network Level Authentication (NLA) for RDP via Registry modifications (`NET-001`) and disable deprecated SMBv1 features (`NET-002`).
- **Microsoft Defender**: Re-enable Real-time Protection if disabled (`DEF-001`).
- **Windows Firewall**: Globally enable all firewall profiles (`FW-001`).
- **Windows Updates**: Force a manual Windows Update check (`UPD-001`).
- **Software CVEs**: Silently patches vulnerabilities using `winget`, gracefully falling back to a manual playbook if automation fails (Phase 23 enhancement).
