# Defiant (Windows Security Audit Tool)

![Platform](https://img.shields.io/badge/Platform-Windows-blue.svg)
![Language](https://img.shields.io/badge/Language-Python_3.10+-yellow.svg)
![Framework](https://img.shields.io/badge/Framework-Flask-lightgrey.svg)
![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-green.svg)

Defiant is a lightweight prototype for auditing Windows security posture. It collects local system data, reports findings with severity levels, calculates a weighted score, and records scan history. The web dashboard also supports reviewing, executing, and rolling back selected hardening actions.

## Screenshots

**Dashboard ready to run an audit**

![Defiant dashboard before an audit](screenshots/dashboard-ready.png)

**Dashboard showing audit results**

![Defiant dashboard with security audit results](screenshots/dashboard-audit-results.png)

## Features

- Audits Defender, firewall settings, local users, installed software and CVEs, services, startup applications, listening ports, password policy, Windows updates, event logs, file integrity, anomalies, registry settings, and vulnerable drivers.
- Calculates a weighted score across 13 categories, with a maximum of 190 points.
- Maps threat-pattern detections to MITRE ATT&CK technique IDs.
- Stores scan history and telemetry in SQLite by default, with optional PostgreSQL support.
- Provides live system telemetry and a browser-based dashboard.
- Supports optional CrowdStrike Falcon IOC lookups. Without Falcon credentials, the threat-intelligence module uses its local IOC data.
- Checks Windows file signatures using the platform's WinVerifyTrust API to help assess process findings.

## Requirements

- Windows 10 or 11
- Python 3.10 or later
- Administrator privileges for checks or remediation actions that require them

## Install and run

From the repository root, create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start the dashboard:

```powershell
python app.py
```

Open <http://127.0.0.1:5000> in a browser and start a scan from the dashboard.

## Configuration

SQLite is used by default; no `.env` file is required for a local SQLite run. To configure PostgreSQL or CrowdStrike Falcon, create a `.env` file in the repository root. Save it as UTF-8 plain text, and do not commit credentials.

To use PostgreSQL, set:

```dotenv
DB_ENGINE=postgres
POSTGRES_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE
```

CrowdStrike Falcon integration is optional. Set these variables to enable it:

```dotenv
FALCON_CLIENT_ID=your-client-id
FALCON_CLIENT_SECRET=your-client-secret
FALCON_BASE_URL=https://api.crowdstrike.com
```

If the Falcon client ID or secret is not set, the application uses the local IOC data instead.

## Project layout

```text
app.py                  Flask dashboard and API
main.py                 Audit orchestration and scoring
database/               SQLite and PostgreSQL persistence
modules/                System collection and audit modules
security/               Remediation and file-signature verification
templates/              Dashboard template
tests/                  Unit tests
```

## Tests

Run the audit scoring tests with:

```powershell
python -m unittest tests/test_audit.py
```

## Safe use

Use this tool only on systems you own or are authorized to assess. Review remediation previews before applying changes. Some checks and remediation actions require elevated privileges.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
