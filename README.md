# Defiant: Windows Security Posture Platform

![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Language](https://img.shields.io/badge/Language-Python_3.10+-yellow.svg)
![Framework](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)
![Database](https://img.shields.io/badge/Database-PostgreSQL_|_SQLite-green.svg)
![Status](https://img.shields.io/badge/Status-Enterprise_Ready-blueviolet.svg)

**Defiant** is an enterprise-grade, lightweight Endpoint Detection and Security Audit platform. It programmatically evaluates a Windows system's security posture, calculates a weighted risk score, stores audit history, provides live telemetry, and offers automated remediation (Hardening) for critical vulnerabilities.

---

## 🎯 Project Overview
This project was designed to automate the traditionally manual process of checking a Windows machine for security misconfigurations. Rather than dumping raw data into a CLI, it aggregates findings through a central Risk Scoring Engine and presents them on a decoupled, modern web dashboard.

### Core Capabilities
<<<<<<< Updated upstream
1. **Automated Auditing (15+ Phases):** Analyzes Windows Defender, Firewalls, User Accounts, Password Policies, Open Ports, Active Services, Startup Apps, Installed Software, Windows Updates, Event Logs, Windows Registry, Software CVEs, File Integrity (FIM), ML Anomaly Detection, and Vulnerable Kernel Drivers (BYOVD).
2. **Smart Verification Engine:** Eliminates false positives natively. Cryptographically validates process Authenticode signatures directly via the Windows kernel (`wintrust.dll`) backed by an ultra-fast, in-memory LRU SQLite cache.
3. **MITRE ATT&CK Mapping:** All detected anomalies and telemetry alerts are natively mapped to their corresponding MITRE ATT&CK vectors for threat intelligence tracking.
4. **Automated Remediation:** Features a "Do No Harm" hardening engine. It allows 1-click automated fixes for safe configurations (like SMB Isolation, NTLM/LAN Manager settings, and Password Lengths).
5. **Centralized Fleet Management:** Built on a Dual-Engine Database architecture. Supports local standalone `SQLite` execution, or dynamic `.env` routing to centralized `PostgreSQL` clusters for managing hundreds of distributed endpoints.
6. **Live Telemetry:** Streams real-time CPU and RAM allocation to the dashboard.
=======
1. **Automated Auditing (14+ Phases):** Analyzes Windows Defender, Firewalls, User Accounts, Password Policies, Open Ports, Active Services, Startup Apps, Installed Software, Windows Updates, Event Logs, Windows Registry, Software CVEs, File Integrity (FIM), and ML Anomaly Detection.
2. **Mathematical Risk Scoring:** Evaluates findings based on Severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and deducts points from 13 distinct, weighted categories to generate an overall health percentage out of 190 total points.
3. **Automated Remediation:** Features a "Do No Harm" hardening engine. It allows 1-click automated fixes for safe configurations (like Password Lengths) while safely flagging complex software uninstalls for manual review.
4. **Live Telemetry:** Streams real-time CPU and RAM allocation to the dashboard.
5. **Persistent Scan History:** Saves every audit mathematically to a local SQLite database for historical compliance tracking.
>>>>>>> Stashed changes

---

## 🏗️ System Architecture

The platform operates on a modular, multi-layer architecture:

1. **Data Collection Layer (`modules/`)**
   - Utilizes `psutil`, `WMI`, `socket`, and `subprocess` (PowerShell) to extract raw operating system data without requiring heavy third-party agents.
2. **Security & Triage Layer (`security/`)**
   - **Verification Engine (`verification.py`):** Utilizes `ctypes` bindings for cryptographic digital signature validation to drop false-positives and whitelist trusted binaries.
   - **Remediation (`remediation.py`):** Safely executes system hardening scripts.
3. **Scoring & Analysis Layer (`modules/score.py`)**
   - Validates the extracted configurations against hardcoded security baselines. Calculates the final score out of 175 points.
4. **Persistence Layer (`database/database.py`)**
   - Powered by `psycopg2` and `python-dotenv`. Stores relational data in Postgres/SQLite with Time-To-Live (TTL) auto-purging logic, intelligent SQL indexing, and schema optimization.
5. **API & Web Layer (`app.py`, `templates/`)**
   - A Flask backend exposes RESTful API endpoints.
   - A modern HTML/JS frontend styled with Tailwind CSS, JetBrains Mono typography, and dynamic threat-metric rendering.

---

## 🚀 Installation & Usage

### Prerequisites
- Windows 10 or 11
- Python 3.10 or higher (or use the pre-compiled `Defiant_Ultimate.exe`)
- Administrator Privileges (Required for automated remediation and deep system audits)

### 1. Database Configuration
By default, Defiant uses a local SQLite database. To route to a centralized PostgreSQL cluster, edit the `.env` file in the root directory:
```env
DB_ENGINE=postgres
POSTGRES_URL=postgresql://user:password@localhost:5432/defiant
```

### 2. Install Dependencies
Open an **Administrator PowerShell** terminal and install the required Python libraries:
```powershell
pip install -r requirements.txt
```

### 3. Start the Platform
Run the backend web server:
```powershell
python app.py
```
*(Alternatively, you can run the standalone compiled executable located at `dist/Defiant_Ultimate/Defiant_Ultimate.exe`)*

### 4. Access the Dashboard
Open any modern web browser (Edge/Chrome/Firefox) and navigate to:
🌐 **http://127.0.0.1:5000**

*(From the dashboard, click **"EXECUTE AUDIT"** to scan your system).*

---

## 📂 Repository Structure

```text
📁 Windows Security Audit Tool/
├── 📄 .env                    # Database configuration (Postgres/SQLite)
├── 📄 app.py                  # Flask Web Server and API router
├── 📄 main.py                 # Core audit execution logic
├── 📄 requirements.txt        # Python dependencies
├── 📁 database/
│   └── 📄 database.py         # Dual-Engine PostgreSQL/SQLite architecture
├── 📁 modules/
│   ├── 📄 defender.py         # Audits Windows Defender status
│   ├── 📄 ports.py            # Outbound Network Telemetry tracking
│   ├── 📄 drivers.py          # Vulnerable Kernel Driver (BYOVD) scanning
│   ├── 📄 score.py            # Mathematical risk scoring engine
│   └── 📄 ... (other audit modules)
├── 📁 security/
│   ├── 📄 remediation.py      # Automated hardening execution scripts
│   └── 📄 verification.py     # C-Types Cryptographic Signature Validation
├── 📁 templates/
│   └── 📄 dashboard.html      # Frontend UI (HTML, CSS, JS)
├── 📁 dist/                   # PyInstaller standalone compiled executables
└── 📁 tests/
    └── 📄 test_audit.py       # Automated unit tests for the scoring math
```

---

## 🧪 Automated Testing
To guarantee the reliability of the Risk Scoring Engine, the mathematical model is heavily tested. To run the automated unit tests:
```powershell
python -m unittest tests/test_audit.py
```

---

## 🛡️ Security Ethics ("Do No Harm")
This tool is built for auditing and defense. The Remediation engine intentionally blocks automated deletion of user data, arbitrary services, or third-party software. Any "CRITICAL" findings in those categories must be remediated manually by a system administrator to ensure business continuity.