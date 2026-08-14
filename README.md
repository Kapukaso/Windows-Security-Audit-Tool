# Defiant: Windows Security Posture Platform

![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Language](https://img.shields.io/badge/Language-Python_3.10+-yellow.svg)
![Framework](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)
![Database](https://img.shields.io/badge/Database-SQLite-green.svg)

**Defiant** is an enterprise-grade, lightweight Endpoint Detection and Security Audit platform. It programmatically evaluates a Windows system's security posture, calculates a weighted risk score, stores audit history, provides live telemetry, and offers automated remediation (Hardening) for critical vulnerabilities.

---

## 🎯 Project Overview
This project was designed to automate the traditionally manual process of checking a Windows machine for security misconfigurations. Rather than dumping raw data into a CLI, it aggregates findings through a central Risk Scoring Engine and presents them on a decoupled, modern web dashboard.

### Core Capabilities
1. **Automated Auditing (10 Phases):** Analyzes Windows Defender, Firewalls, User Accounts, Password Policies, Open Ports, Active Services, Startup Apps, Installed Software, Windows Updates, and Event Logs.
2. **Mathematical Risk Scoring:** Evaluates findings based on Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and deducts points from 10 distinct, weighted categories to generate an overall health percentage out of 135 total points.
3. **Automated Remediation:** Features a "Do No Harm" hardening engine. It allows 1-click automated fixes for safe configurations (like Password Lengths) while safely flagging complex software uninstalls for manual review.
4. **Live Telemetry:** Streams real-time CPU and RAM allocation to the dashboard.
5. **Persistent Scan History:** Saves every audit mathematically to a local SQLite database for historical compliance tracking.

---

## 🏗️ System Architecture

The platform operates on a modular, multi-layer architecture:

1. **Data Collection Layer (`modules/`)**
   - Utilizes `psutil`, `WMI`, `socket`, and `subprocess` (PowerShell) to extract raw operating system data without requiring heavy third-party agents.
2. **Scoring & Analysis Layer (`modules/score.py`)**
   - Validates the extracted configurations against hardcoded security baselines. Calculates the final score.
3. **Persistence Layer (`database/database.py`)**
   - Stores relational data in `audit_history.db` (Tables: `scans`, `findings`).
4. **API & Web Layer (`app.py`, `templates/`)**
   - A Flask backend exposes RESTful API endpoints (`/api/scan`, `/api/history`, `/api/telemetry`).
   - A modern JavaScript/HTML frontend (inspired by EDRs like CrowdStrike) consumes the API asynchronously via `fetch`.

---

## 🚀 Installation & Usage

### Prerequisites
- Windows 10 or 11
- Python 3.10 or higher
- Administrator Privileges (Required for automated remediation and deep system audits)

### 1. Install Dependencies
Open an **Administrator PowerShell** terminal and install the required Python libraries:
```powershell
pip install -r requirements.txt
```

### 2. Start the Platform
Run the backend web server:
```powershell
python app.py
```

### 3. Access the Dashboard
Open any modern web browser (Edge/Chrome/Firefox) and navigate to:
👉 **http://127.0.0.1:5000**

*(From the dashboard, click **"INITIATE AUDIT"** to scan your system).*

---

## 📁 Repository Structure

```text
📂 Windows Security Audit Tool/
├── 📄 app.py                  # Flask Web Server and API router
├── 📄 main.py                 # Core audit execution logic
├── 📄 requirements.txt        # Python dependencies
├── 📂 database/
│   └── 📄 database.py         # SQLite schema and history retrieval
├── 📂 modules/
│   ├── 📄 defender.py         # Audits Windows Defender status
│   ├── 📄 firewall.py         # Audits Windows Firewall rules
│   ├── 📄 password_policy.py  # Audits Net Accounts policies
│   ├── 📄 score.py            # Mathematical risk scoring engine
│   └── 📄 ... (other audit modules)
├── 📂 security/
│   └── 📄 remediation.py      # Automated hardening execution scripts
├── 📂 templates/
│   └── 📄 dashboard.html      # Frontend UI (HTML, CSS, JS)
└── 📂 tests/
    └── 📄 test_audit.py       # Automated unit tests for the scoring math
```

---

## 🧪 Automated Testing
To guarantee the reliability of the Risk Scoring Engine, the mathematical model is heavily tested. To run the automated unit tests:
```powershell
python -m unittest tests/test_audit.py
```

---

## 🔒 Security Ethics ("Do No Harm")
This tool is built for auditing and defense. The Remediation engine intentionally blocks automated deletion of user data, arbitrary services, or third-party software. Any "CRITICAL" findings in those categories must be remediated manually by a system administrator to ensure business continuity.