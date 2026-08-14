# Project Outline & Code Mapping

This document maps the official 11-point security outline directly to the programmatic modules built into the **Defiant Windows Security Posture Platform**. This proves that the platform satisfies the comprehensive security requirements.

### 1. Update and Patch Management
* **Requirement:** Regularly update the OS and applications.
* **Our Implementation:** **Phase 10 (`modules/updates.py`)** explicitly uses WMI (`Win32_QuickFixEngineering`) to check the exact installation dates of Windows Hotfixes, raising a `HIGH` vulnerability if patches are older than 30 days.

### 2. Secure Configuration
* **Requirement:** Disable unnecessary services and configure firewall settings.
* **Our Implementation:** **Phase 3 (`modules/firewall.py`)** ensures Domain, Private, and Public firewalls are strictly ON. **Phase 6 (`modules/services.py`)** audits all running background services for privilege escalation vulnerabilities.

### 3. User Accounts and Privileges
* **Requirement:** Implement Least Privilege (PoLP) and use strong passwords.
* **Our Implementation:** **Phase 4 (`modules/users.py`)** actively hunts for unauthorized accounts in the Local Administrators group. **Phase 9 (`modules/password_policy.py`)** audits the OS password length and lockout policies to defend against brute-forcing.

### 4. File System Security
* **Requirement:** Enable auditing and logging.
* **Our Implementation:** **Phase 10 (`modules/event_logs.py`)** actively polls the Windows Security Event Log to ensure forensic auditing is enabled and accessible.

### 5. Network Security
* **Requirement:** Disable unused network ports and protocols.
* **Our Implementation:** **Phase 8 (`modules/ports.py`)** maps every active `LISTEN` socket on the machine, specifically flagging dangerous legacy protocols like Telnet (23), SMBv1 (445), and FTP (21).

### 6. Malware Protection
* **Requirement:** Install and configure antivirus software.
* **Our Implementation:** **Phase 2 (`modules/defender.py`)** utilizes deep PowerShell introspection to verify that Microsoft Defender's Real-Time Protection and Behavior Monitoring (Heuristics) are not just installed, but actively running.

### 7. Backup and Recovery
* **Requirement:** Establish a backup strategy.
* **Our Implementation:** Handled via organizational policy rather than a local endpoint script, though our platform's **Database History (Phase 13)** acts as a backup of the system's security compliance states over time.

### 8. Monitoring and Logging
* **Requirement:** Enable system logging and monitor system anomalies.
* **Our Implementation:** **Phase 14 (Web Dashboard)** features a Live Telemetry engine using `psutil` to stream real-time CPU and RAM allocation metrics directly to the interface, acting as a lightweight anomaly monitor.

### 9. Security Policies and Procedures
* **Requirement:** Enforce security policies.
* **Our Implementation:** **Phase 15 (Remediation Engine)** actively *enforces* policies. When a weak password policy is found, the platform can automatically deploy a fix (`net accounts /minpwlen:8`) via the dashboard.

### 10. Regular Security Audits
* **Requirement:** Conduct regular vulnerability assessments.
* **Our Implementation:** The entire **Defiant Platform** is a 1-click, automated vulnerability assessment tool designed precisely for this purpose.

### 11. Continual Improvement
* **Requirement:** Review and update security measures regularly.
* **Our Implementation:** By structuring the code into highly decoupled Python modules (`modules/`), the platform was designed for continual improvement. New security checks can be dropped into the folder without breaking the core Scoring Engine.
