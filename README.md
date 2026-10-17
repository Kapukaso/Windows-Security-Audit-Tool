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

- **Comprehensive Security Auditing**: Audits Defender, firewall settings, local users, installed software and CVEs, running services, startup applications, listening ports, password policy, Windows updates, event logs, file integrity, ML anomalies, registry hardening, and vulnerable drivers.
- **Risk Scoring Engine**: Calculates a mathematically grounded weighted score across 13 security categories, with a maximum of 190 points.
- **Multi-Standard Compliance**: Real-time compliance assessment mapping findings against CIS Benchmarks, NIST SP 800-53, ISO/IEC 27001, and HIPAA Security Rule controls.
- **Two-Step Reversible Remediation**: Playbook-driven hardening actions with impact preview, approval gating for high-risk actions, safe-only enforcement, and one-click rollback.
- **Dual-Engine Persistence**: Seamless persistence supporting SQLite and enterprise PostgreSQL clusters with schema parity, high-speed indexing, and automated data retention pruning.
- **Threat Intelligence & MITRE Mapping**: Optional CrowdStrike Falcon IOC lookups with offline fallback database, process SHA-256 matching, and MITRE ATT&CK technique mapping.
- **High-Performance Caching & Resiliency**: Persistent local NIST NVD CVE cache with circuit breaker, bounded 24-hour event log queries, and WinVerifyTrust Authenticode signature caching.
- **Single-Port HUD Dashboard**: Sleek browser-based sci-fi HUD (http://127.0.0.1:5000) featuring live CPU/RAM telemetry, scan progress tracking, and toast notifications.
- **API Security**: Constant-time token verification (`@require_auth`) for all mutating endpoints.

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

SQLite is used by default; no `.env` file is required for a local SQLite run. To configure PostgreSQL, CrowdStrike Falcon, or custom API authentication, create a `.env` file in the repository root. Save it as UTF-8 plain text, and do not commit credentials.

To configure API key authentication for mutating actions:

```dotenv
# API Authentication (Optional - if unset, an ephemeral 32-byte key is generated at startup)
DEFIANT_API_KEY=your-secure-api-key-here
```

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
app.py                  Flask dashboard and REST API
main.py                 Audit orchestration and scoring
database/               SQLite and PostgreSQL persistence with TTL pruning
documentation/          Full technical documentation and phase guides
modules/                System collection, compliance, and audit modules
security/               Remediation playbooks, rollback, and WinTrust verification
templates/              HUD dashboard and report templates
tests/                  Hermetic mock unit tests (Pytest)
```

## Tests

Run the complete 61-test unit and mock test suite with:

```powershell
python -m pytest tests/ -v
```

All tests are hermetic and run fully offline without requiring Windows Administrator elevation by utilizing comprehensive mocks for WMI, PowerShell, WinTrust ctypes, and network endpoints.

## Documentation

Comprehensive architectural documentation and phase breakdown guides are available in the [documentation/](documentation/index.md) directory:
- [API Reference](documentation/API_Reference.md): REST API endpoints and authentication.
- [Developer Guide](documentation/Developer_Guide.md): Extending modules and remediation playbooks.
- [Database & UI Architecture](documentation/Database_and_UI_Architecture.md): Dual-engine persistence and HUD design.
- [Enterprise Workflow & Threat Intel](documentation/Enterprise_Workflow_and_Intel.md): Playbooks, rollbacks, and Falcon integration.

## Safe use

Use this tool only on systems you own or are authorized to assess. Review remediation previews before applying changes. Some checks and remediation actions require elevated privileges.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
