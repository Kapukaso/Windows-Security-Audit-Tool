---
last_mapped_commit: f61906e15b5f40f34417ffe3a12a6a7015696188
last_mapped_at: 2026-10-17
---
# Codebase Structure

**Analysis Date:** 2026-10-17

## Directory Layout

```
Windows Security Audit Tool/
├── app.py                      # Flask web dashboard and REST API server
├── main.py                     # CLI orchestrator and concurrent audit runner
├── audit_history.db            # Default local SQLite database file
├── Defiant_Ultimate.spec       # PyInstaller standalone build configuration
├── requirements.txt            # Python package dependencies
├── README.md                   # Project overview, installation, and usage
├── LICENSE                     # MIT license file
├── .env                        # Local environment variables (DB, Falcon credentials)
├── .defiant_config.json        # Local configuration file (NVD API key)
├── database/                   # Persistence engine (SQLite / PostgreSQL)
│   └── database.py             # Schema definition, migrations, and CRUD operations
├── modules/                    # Core system security audit and collection modules
│   ├── compliance.py           # Regulatory framework mapping (CIS, NIST, STIG, etc.)
│   ├── cve_lookup.py           # NIST NVD API vulnerability lookup
│   ├── defender.py             # Windows Defender preferences and status collector
│   ├── drivers.py              # Windows vulnerable/outdated driver auditing
│   ├── event_logs.py           # Security event log anomaly detection
│   ├── fim.py                  # File Integrity Monitoring (FIM) baseline tracker
│   ├── firewall.py             # Windows Firewall state and rule assessment
│   ├── ml_anomaly.py           # Machine learning telemetry anomaly detector
│   ├── password_policy.py      # Windows local password and lockout policy audit
│   ├── ports.py                # Listening network ports and socket audit
│   ├── registry.py             # High-risk Windows registry hardening checks
│   ├── report.py               # JSON and HTML audit report generator
│   ├── score.py                # 190-point scoring algorithm and severity deductions
│   ├── services.py             # Windows services and unquoted path audit
│   ├── software.py             # Installed software inventory collector
│   ├── startup.py              # Startup programs and persistence checks
│   ├── system.py               # OS version, hostname, and CPU/RAM info collector
│   ├── threat_intel.py         # MITRE ATT&CK detection and Falcon IOC queries
│   └── users.py                # Local user account and guest status auditor
├── security/                   # Hardening playbooks and cryptographic verification
│   ├── remediation.py          # Playbook preview, execution, and rollback engine
│   └── verification.py         # WinVerifyTrust Authenticode signature validator
├── templates/                  # Server-rendered Jinja2 HTML templates
│   ├── dashboard.html          # Full interactive web HUD and remediation interface
│   └── report.html             # Standalone exportable security audit report template
├── utils/                      # Helper libraries and cross-cutting utilities
│   ├── constants.py            # Global constants and scoring thresholds
│   ├── display.py              # ANSI color and console formatting helpers
│   ├── logger.py               # Application logging initialization
│   └── powershell.py           # Subprocess wrapper for raw and JSON PowerShell output
├── tests/                      # Automated unit test suite
│   └── test_audit.py           # Unit tests for scoring logic and boundary constraints
├── node_frontend/              # Optional Express-based static frontend wrapper
│   ├── package.json            # Node.js project manifest (Express, CORS)
│   ├── server.js               # Express static web server listening on port 3000
│   └── public/                 # Static web client assets (HTML/CSS/JS)
├── reports/                    # Generated output directory for audit scans
│   ├── audit_report_*.html     # Generated HTML security reports
│   └── audit_report_*.json     # Exported JSON security reports
├── documentation/              # Project specifications, guides, and phase history
│   ├── index.md                # Documentation index
│   ├── API_Reference.md        # Detailed documentation for REST endpoints
│   ├── Developer_Guide.md      # Development setup and contributor instructions
│   └── Phase_01_*.md           # Historical milestone documentation for phases 1-24
└── .planning/                  # GSD planning directory
    └── codebase/               # Codebase mapping reference documents
```

## Directory Purposes

**`modules/`:**
- Purpose: Contains all modular security auditing collectors, threat intelligence, ML models, and scoring logic
- Contains: Individual Python files exporting collection and assessment functions
- Key files: `modules/score.py`, `modules/threat_intel.py`, `modules/compliance.py`, `modules/cve_lookup.py`

**`security/`:**
- Purpose: Active defense controls, automated remediation actions, and cryptographic file integrity checks
- Contains: Native Windows C-types bindings and playbook execution scripts
- Key files: `security/remediation.py`, `security/verification.py`

**`database/`:**
- Purpose: Unified data persistence layer for SQLite and PostgreSQL
- Contains: Schema initialization, scan recording, telemetry logging, and history queries
- Key files: `database/database.py`

**`utils/`:**
- Purpose: Shared utility functions for process execution and terminal display
- Contains: PowerShell subprocess wrappers and logging helpers
- Key files: `utils/powershell.py`, `utils/logger.py`

**`templates/`:**
- Purpose: Presentation layer for Flask server-rendered UI and reports
- Contains: HTML templates with embedded JavaScript and CSS
- Key files: `templates/dashboard.html`, `templates/report.html`

**`tests/`:**
- Purpose: Test automation suite
- Contains: Unit tests validating scoring, deductions, and floor limits
- Key files: `tests/test_audit.py`

**`node_frontend/`:**
- Purpose: Optional alternative web server serving static dashboard assets
- Contains: Express server configuration and public frontend bundle
- Key files: `node_frontend/server.js`, `node_frontend/package.json`

## Key File Locations

**Entry Points:**
- `app.py`: Web dashboard and REST API server
- `main.py`: Command-line audit execution script
- `node_frontend/server.js`: Node.js frontend server

**Configuration:**
- `.env`: Environment variables for database engines and CrowdStrike Falcon credentials
- `.defiant_config.json`: Local configuration for NVD API keys
- `Defiant_Ultimate.spec`: PyInstaller executable packaging specification

**Core Logic:**
- `modules/score.py`: Scoring algorithm, category weights, and severity deductions
- `security/remediation.py`: Hardening playbook definitions and rollback mechanisms
- `database/database.py`: Relational database operations and connection management

**Testing:**
- `tests/test_audit.py`: Unit tests for scoring engine behavior

## Naming Conventions

**Files:**
- Python modules: `lowercase_snake_case.py` (e.g., `modules/password_policy.py`, `security/remediation.py`)
- Documentation: `Title_Case_With_Underscores.md` or `UPPERCASE.md` (e.g., `documentation/Developer_Guide.md`, `README.md`)
- Templates: `lowercase.html` (e.g., `templates/dashboard.html`)

**Functions and Variables:**
- Python functions: `snake_case` (e.g., `run_full_audit()`, `get_defender_status()`, `calculate_score()`)
- Constants and Playbook registries: `UPPER_SNAKE_CASE` (e.g., `CATEGORY_WEIGHTS`, `SEVERITY_DEDUCTIONS`, `PLAYBOOKS`)
- Classes: `PascalCase` (e.g., `TestSecurityPlatform`, `WINTRUST_DATA`)

## Where to Add New Code

**New Audit Check / Module:**
- Collector file: Create `modules/<feature_name>.py` exposing `get_<feature>()` and `assess_<feature>()` returning structured findings
- Wire up concurrent task: Import and register the new task inside `main.py:run_full_audit()` `tasks` dict
- Category weight: Add weight definition to `modules/score.py:CATEGORY_WEIGHTS`
- Compliance mapping: Add corresponding regulatory cross-references to `modules/compliance.py:COMPLIANCE_MAPPINGS`
- Tests: Add unit tests in `tests/test_audit.py` (or new `tests/test_<feature>.py`)

**New Hardening Remediation:**
- Definition: Add new playbook entry to `security/remediation.py:PLAYBOOKS` specifying `finding_id`, `description`, `risk_level`, `preview`, `execute_cmd`, `rollback_cmd`, and `type`
- Frontend UI: The dashboard in `templates/dashboard.html` dynamically queries `/api/remediate/preview` based on finding IDs

**New Utility Helper:**
- Common helpers: Place inside `utils/<helper_name>.py` and export cleanly

## Special Directories

**`reports/`:**
- Purpose: Stores generated JSON and HTML scan reports from CLI or web triggers
- Generated: Yes (created dynamically at runtime)
- Committed: Partial (sample reports are present in repo)

**`dist/` & `build/`:**
- Purpose: PyInstaller compilation artifacts and standalone executables
- Generated: Yes
- Committed: No (managed by `.gitignore`)

**`.planning/`:**
- Purpose: GSD workflow state, specifications, and codebase maps
- Generated: Yes
- Committed: Yes

---

*Structure analysis: 2026-10-17*
