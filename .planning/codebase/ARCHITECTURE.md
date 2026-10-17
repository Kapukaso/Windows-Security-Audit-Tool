---
last_mapped_commit: f61906e15b5f40f34417ffe3a12a6a7015696188
last_mapped_at: 2026-10-17
---
<!-- refreshed: 2026-10-17 -->

# Architecture

**Analysis Date:** 2026-10-17

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    Presentation / API Entry Points                       │
├───────────────────────────────────┬─────────────────────────────────────┤
│   Flask Dashboard & REST API      │     Node.js Frontend Server         │
│   `app.py` (Port 5000)            │     `node_frontend/server.js` (3000)│
│   `templates/dashboard.html`      │     `node_frontend/public/`         │
└─────────────────┬─────────────────┴──────────────────┬──────────────────┘
                  │                                    │
                  ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Audit Orchestration Layer                           │
│   `main.py:run_full_audit()` (Concurrent ThreadPoolExecutor)            │
└─────────────────┬───────────────────────────────────────────────────────┘
                  │
        ┌─────────┴────────────────────────────────┐
        ▼                                          ▼
┌───────────────────────────────┐        ┌────────────────────────────────┐
│   System Audit Modules        │        │  Advanced Threat & Intel       │
│   (`modules/`)                │        │  (`modules/`, `security/`)     │
│   - defender, firewall        │        │  - threat_intel (MITRE ATT&CK) │
│   - users, password_policy    │        │  - cve_lookup (NIST NVD)       │
│   - updates, event_logs       │        │  - ml_anomaly (IsolationForest)│
│   - ports, services, startup  │        │  - fim (File Integrity)        │
│   - registry, drivers         │        │  - verification (WinTrust)     │
└───────────────┬───────────────┘        └────────────────┬───────────────┘
                │                                         │
                └───────────────────┬─────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                Scoring, Compliance & Remediation Engines                │
│   - `modules/score.py` (Weighted 190pt ceiling, severity deductions)    │
│   - `modules/compliance.py` (CIS, NIST, STIG, ISO 27001, HIPAA, PCI)   │
│   - `security/remediation.py` (Preview, execution, rollback playbooks)  │
│   - `modules/report.py` (HTML/JSON artifact generation)                 │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Persistence Layer                                │
│   `database/database.py` (Dual engine: SQLite / PostgreSQL)             │
│   - `audit_history.db` (Local SQLite)                                   │
│   - `scans`, `findings`, `telemetry_log`, `remediation_log` tables      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Flask API Server** | Exposes HTTP endpoints for scans, telemetry, remediation actions, and serves dashboard UI | `app.py` |
| **Audit Orchestrator** | Coordinates concurrent module execution using `ThreadPoolExecutor` and tracks progress | `main.py` |
| **System Collectors** | Interrogate OS subsystems (Defender, Firewall, Users, Services, Ports, Registry, Drivers, Logs) | `modules/*.py` |
| **CVE Engine** | Queries NIST NVD REST API to identify published vulnerabilities in installed software | `modules/cve_lookup.py` |
| **Threat Intelligence** | Correlates running processes with MITRE ATT&CK techniques, hashes, and CrowdStrike Falcon / local IOCs | `modules/threat_intel.py` |
| **ML Anomaly Engine** | Detects behavioral telemetry outliers using an unsupervised `IsolationForest` model | `modules/ml_anomaly.py` |
| **FIM Subsystem** | Tracks critical Windows binary hash baselines and detects unauthorized modifications | `modules/fim.py` |
| **Signature Verifier** | Performs native Authenticode digital signature validation via Win32 `wintrust.dll` | `security/verification.py` |
| **Scoring Engine** | Calculates weighted category scores (max 190 points) applying severity-based deductions | `modules/score.py` |
| **Compliance Mapper** | Cross-references security findings against CIS, NIST, STIG, ISO 27001, HIPAA, and PCI DSS | `modules/compliance.py` |
| **Remediation Engine** | Executes automated hardening scripts with safe preview, approval gating, and rollback capabilities | `security/remediation.py` |
| **Database Connector** | Manages relational storage and schema migrations across SQLite and PostgreSQL | `database/database.py` |
| **Node.js Frontend** | Standalone static web server hosting the dashboard UI | `node_frontend/server.js` |

## Pattern Overview

**Overall:** Modular concurrent pipeline with decoupled data collection, centralized scoring, and safety-gated remediation.

**Key Characteristics:**
- **Asynchronous Fan-Out:** Audit tasks run concurrently across 16 threads in `main.py:run_full_audit` to minimize execution time on large Windows installations.
- **Fail-Soft Isolation:** Each collector module wraps its OS queries in try/except blocks, returning graceful fallback finding dictionaries rather than terminating the audit.
- **Safety-First Remediation:** Every playbook in `security/remediation.py` includes a deterministic `preview`, risk classification (`SAFE`, `MEDIUM`, `HIGH`), execution command, and reversible `rollback_cmd`.
- **Dual-Engine Persistence:** Database operations in `database/database.py` transparently switch between SQLite and PostgreSQL based on `DB_ENGINE`.

## Layers

**Presentation Layer:**
- Purpose: Render live HUD metrics, trigger audits, inspect findings, and trigger playbooks
- Location: `app.py`, `templates/dashboard.html`, `node_frontend/`
- Contains: Flask routes, Jinja templates, client-side JS event handlers, chart visualizations
- Depends on: Audit orchestrator, database, remediation engine
- Used by: Web browsers connecting to `http://localhost:5000` or `http://localhost:3000`

**Orchestration Layer:**
- Purpose: Coordinate multi-threaded security checks and broadcast progress percentages
- Location: `main.py`
- Contains: `run_full_audit`, `ThreadPoolExecutor` worker loops, dictionary aggregation
- Depends on: All individual modules in `modules/`
- Used by: `app.py` and direct CLI execution

**Collection & Analysis Layer:**
- Purpose: Extract system posture, inspect telemetry, query threat feeds, and identify CVEs
- Location: `modules/*.py`, `security/verification.py`
- Contains: WMI queries, PowerShell wrappers, Win32 ctypes calls, NIST NVD HTTP queries
- Depends on: `psutil`, `utils/powershell.py`, `ctypes.windll.wintrust`
- Used by: Orchestration layer

**Scoring & Assessment Layer:**
- Purpose: Normalize raw findings into structured severities and score out of 190 points
- Location: `modules/score.py`, `modules/compliance.py`, `modules/report.py`
- Contains: Category weights, severity penalty matrices, compliance regulatory mappings
- Depends on: Findings dictionaries produced by collection layer
- Used by: Orchestration layer, API responses, report generators

**Remediation & Defense Layer:**
- Purpose: Hardening execution, process isolation, and configuration rollbacks
- Location: `security/remediation.py`, `security/verification.py`
- Contains: Playbook dictionary `PLAYBOOKS`, subprocess/powershell runners, Authenticode verifier
- Depends on: Database (for action logging), PowerShell
- Used by: Flask API endpoints (`/api/remediate/*`)

**Data Persistence Layer:**
- Purpose: Save audit histories, individual findings, telemetry metrics, and remediation logs
- Location: `database/database.py`
- Contains: DDL schemas, index definitions, CRUD operations for scans and telemetry
- Depends on: `sqlite3`, `psycopg2`
- Used by: `app.py`, `main.py`, `modules/ml_anomaly.py`, `security/remediation.py`

## Data Flow

### Primary Audit Scan Path

1. User clicks "Run Audit" in dashboard or executes CLI: sends `POST /api/scan` (`app.py:38`)
2. Orchestrator initializes tasks and executes 16 collector functions in parallel (`main.py:run_full_audit` at line 92)
3. Progress dictionary `SCAN_PROGRESS` is updated sequentially as tasks complete; queried by frontend via `GET /api/scan/progress` (`app.py:32`)
4. Aggregated findings and module outputs are evaluated by `calculate_score` (`modules/score.py:32`)
5. Full results are committed to database via `save_scan_results` (`database/database.py:102`)
6. Compliance report is generated via `generate_compliance_report` (`modules/compliance.py:70`)
7. Response JSON containing scan ID, score, findings, and compliance data is returned to the web HUD (`app.py:65`)

### Remediation Execution Flow

1. User requests remediation preview via `POST /api/remediate/preview` (`app.py:79`)
2. `security/remediation.py:get_remediation_preview` returns risk level, description, and command text
3. User confirms action; frontend sends `POST /api/remediate/execute` with approval flag (`app.py:85`)
4. `security/remediation.py:execute_remediation` verifies approval if risk is HIGH/MEDIUM, runs command, and logs action to database table `remediation_log`
5. User can subsequently invoke `POST /api/remediate/rollback` (`app.py:97`) to reverse the configuration change

**State Management:**
- Application state is held transiently in `app.py` global dictionaries (`LATEST_SCAN`, `SCAN_PROGRESS`) and persisted in `audit_history.db` (or PostgreSQL).
- File integrity states are tracked across scans in the `fim_baselines` database table.

## Key Abstractions

**Finding Schema:**
- Purpose: Universal format for all audit observations across all 16 modules
- Examples: `modules/software.py`, `modules/defender.py`, `modules/ports.py`
- Pattern: Dictionary with keys:
  - `id`: Unique finding string (e.g., `DEF-001`, `NET-001`, `CVE-2023-...`, `ML-001`)
  - `category`: Category name matching `CATEGORY_WEIGHTS` (e.g., `Defender`, `Updates`, `Registry`)
  - `severity`: Standard severity level (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`)
  - `title`: Short human-readable summary
  - `description`: Detailed technical explanation and impact

**Remediation Playbook:**
- Purpose: Self-contained definition of a hardening action and its exact inversion
- Examples: `security/remediation.py:PLAYBOOKS`
- Pattern: Dictionary defining `finding_id`, `description`, `risk_level`, `preview`, `execute_cmd`, `rollback_cmd`, and `type` (`powershell` or `subprocess`)

## Entry Points

**Flask Web Application:**
- Location: `app.py`
- Triggers: `python app.py` (serves on `http://127.0.0.1:5000`)
- Responsibilities: HTTP API handling, real-time telemetry streaming, static asset and template serving

**CLI Orchestrator:**
- Location: `main.py`
- Triggers: `python main.py`
- Responsibilities: Console terminal audit execution, formatted table printing (`tabulate`), HTML/JSON report generation

**Node.js Static Server:**
- Location: `node_frontend/server.js`
- Triggers: `npm start` in `node_frontend/` (serves on `http://localhost:3000`)
- Responsibilities: Serving static web assets and client-side HUD

## Architectural Constraints

- **Platform Dependent:** Requires Windows operating system due to `ctypes.windll.wintrust`, Windows PowerShell commands (`MpPreference`, `netsh advfirewall`), and Windows registry paths (`HKLM:\...`).
- **Administrative Privileges:** Must be run in an elevated administrator context (UAC elevated) to query Defender settings, raw event logs, and execute remediation playbooks.
- **Threading Model:** Multi-threaded I/O via Python `ThreadPoolExecutor`. Background scan progress communicates via shared memory dictionaries (`SCAN_PROGRESS`).
- **Global State in Flask:** Scan cache (`LATEST_SCAN`) and progress (`SCAN_PROGRESS`) are stored in module-level global variables in `app.py`, limiting concurrent scans to single-tenant usage.

## Anti-Patterns

### Unhandled Rate Limiting in External Loops

- **What happens:** In `modules/cve_lookup.py`, NVD API queries are executed with fixed delays in loops, but can encounter timeouts or HTTP 403/429 without exponential backoff.
- **Why it's wrong:** Large software inventories can slow down total scan time or fail silently without recording which lookups timed out.
- **Do this instead:** Implement cached vulnerability lookups and batch requests or local CVE databases as seen in `modules/threat_intel.py:LOCAL_IOC_DATABASE`.

### Direct In-Memory Progress Tracking

- **What happens:** `SCAN_PROGRESS` in `app.py` is a mutable dictionary modified across threads without an explicit synchronization lock (`threading.Lock`).
- **Why it's wrong:** Potential race condition when multiple requests hit `/api/scan` and `/api/scan/progress` simultaneously.
- **Do this instead:** Use thread-safe queues or atomic state containers for task tracking.

## Error Handling

**Strategy:** Defensive isolation per module to prevent complete audit failure when one Windows API call is denied or fails.

**Patterns:**
- Try/except blocks around each individual task in `main.py` and `modules/*.py`.
- On PowerShell execution failure in `utils/powershell.py`, returns `None` or structured error dictionaries `{"error": "PowerShell execution failed."}`.
- On ML failure in `modules/ml_anomaly.py`, generates an `INFO` finding (`ML-ERR`) rather than throwing an unhandled exception.

## Cross-Cutting Concerns

**Logging:** Console and file logging initialized in `utils/logger.py` (`setup_logger`), plus transactional database audit logging in `security/remediation.py:log_remediation_action`.
**Validation:** `security/verification.py` Authenticode cryptographic validation using `WinVerifyTrust` Win32 API.
**Authentication:** Relies on Windows host security boundaries; no application-level authentication on local HTTP endpoints.

---

*Architecture analysis: 2026-10-17*
