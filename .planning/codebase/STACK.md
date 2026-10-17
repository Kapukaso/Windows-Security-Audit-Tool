---
last_mapped_commit: f61906e15b5f40f34417ffe3a12a6a7015696188
last_mapped_at: 2026-10-17
---
# Technology Stack

**Analysis Date:** 2026-10-17

## Languages

**Primary:**
- Python 3.10+ - Backend audit orchestrator, scoring engine, security remediations, and Flask web API (`app.py`, `main.py`, `modules/*.py`, `security/*.py`, `database/*.py`)

**Secondary:**
- JavaScript (Node.js & Browser ES6) - Frontend dashboard server (`node_frontend/server.js`) and client-side HUD dashboard rendering (`templates/dashboard.html`, `node_frontend/public/index.html`)
- PowerShell / Command Shell - Subprocess invocations for deep Windows system auditing, MpPreference, registry, firewall, and remediation tasks (`utils/powershell.py`, `security/remediation.py`)
- HTML5 / CSS3 / Jinja2 - Web dashboard layout, reports styling, and audit summary templates (`templates/dashboard.html`, `templates/report.html`)

## Runtime

**Environment:**
- Python 3.10+ on Windows 10/11 (CPython)
- Node.js (Optional frontend static server: `node_frontend/server.js`)

**Package Manager:**
- Python: `pip` via `requirements.txt`
  - Lockfile: missing (dependencies are unpinned in `requirements.txt`)
- Node.js: `npm` in `node_frontend/`
  - Lockfile: `node_frontend/package-lock.json` present

## Frameworks

**Core:**
- Flask 2.x/3.x (`app.py`) - REST API and web dashboard serving endpoints (`/api/scan`, `/api/remediate/*`, `/api/telemetry`, `/api/history`)
- Flask-CORS (`app.py`) - Cross-Origin Resource Sharing handling between Flask backend (port 5000) and frontend (port 3000)
- Express 4.18.2 (`node_frontend/server.js`) - Lightweight static server hosting frontend assets
- Windows native APIs via `ctypes` (`security/verification.py`) - Authenticode signature verification via `wintrust.dll` (WinVerifyTrust)

**Machine Learning & Data:**
- scikit-learn (`modules/ml_anomaly.py`) - Unsupervised behavioral anomaly detection via `IsolationForest`
- numpy (`modules/ml_anomaly.py`) - Numeric baseline generation and telemetry vector manipulation
- pandas (`requirements.txt`, `modules/report.py`) - Structured audit data aggregation and tabular transformations
- psutil (`modules/system.py`, `modules/threat_intel.py`, `modules/ml_anomaly.py`, `app.py`) - Cross-platform process and system telemetry

**Testing:**
- Python `unittest` (`tests/test_audit.py`) - Automated test suite for scoring calculations, deductions, and boundary floors

**Build/Dev:**
- PyInstaller (`Defiant_Ultimate.spec`) - Windows standalone executable packager

## Key Dependencies

**Critical:**
- `psutil` - Process enumeration, open network sockets, resource telemetry
- `flask` & `flask-cors` - Web dashboard server and remediation execution API
- `sqlite3` (standard library) / `psycopg2` - Dual-engine database persistence layer
- `wmi` & `utils/powershell.py` - Windows Management Instrumentation and PowerShell script bridge
- `tabulate` & `colorama` - Console table formatting and ANSI terminal status highlighting

**Infrastructure:**
- `python-dotenv` - Environment variable loading from `.env`
- `jinja2` - HTML report generation template engine

## Configuration

**Environment:**
- `.env` in repository root (loaded by `python-dotenv` in `database/database.py`, `modules/threat_intel.py`):
  - `DB_ENGINE`: `sqlite` (default) or `postgres`
  - `POSTGRES_URL`: PostgreSQL connection string (e.g. `postgresql://USER:PASSWORD@HOST:5432/DATABASE`)
  - `FALCON_CLIENT_ID`: CrowdStrike Falcon OAuth2 Client ID (optional)
  - `FALCON_CLIENT_SECRET`: CrowdStrike Falcon OAuth2 Client Secret (optional)
  - `FALCON_BASE_URL`: Falcon API base URL (default: `https://api.crowdstrike.com`)
- `~/.defiant_config.json` or `.defiant_config.json`:
  - `NVD_API_KEY`: API key for NIST NVD vulnerability lookup (`modules/cve_lookup.py`)

**Build:**
- `Defiant_Ultimate.spec`: PyInstaller bundling configuration bundling `templates/` and `.env` with hidden imports for `psycopg2` and `dotenv`

## Platform Requirements

**Development:**
- Windows 10 or Windows 11 (required for Win32 API ctypes, Defender WMI, WinVerifyTrust, netsh, MpPreference)
- Python 3.10+ (x64)
- Local Administrator privileges required to inspect Defender preferences, Windows event logs, network firewall rules, and apply hardening actions

**Production:**
- Standalone Windows binary bundle (`dist/Defiant_Ultimate/`) or direct execution under Windows service / local admin shell

---

*Stack analysis: 2026-10-17*
