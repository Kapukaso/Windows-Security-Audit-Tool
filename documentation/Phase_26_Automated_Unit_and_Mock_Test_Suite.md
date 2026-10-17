# Phase 26: Automated Unit & Mock Test Suite

## 26.1 Overview
Phase 26 establishes end-to-end automated verification across all layers of the Defiant security platform. By decoupling testing from live host dependencies and physical Windows Administrator privileges, the platform achieves fast, reproducible, and regression-free development cycles.

---

## 26.2 Test Architecture & Scope

The test suite is structured into five core test modules in `tests/`:

### 1. `tests/test_audit_modules.py` (Audit Collectors & Assessment)
Verifies all 16 collection modules:
* `defender`: Real-time protection enabled/disabled, outdated signatures, fallback handling.
* `firewall`: Domain, Private, and Public profile assessment and offline fallback.
* `users`: Admin account enumeration, guest account enablement.
* `password_policy`: Complexity enforcement, length thresholds, NTLMv2 checks.
* `software` & `cve_lookup`: Registry uninstallation enumeration, local CVE cache hits, circuit-breaker timeout behavior.
* `services` & `ports`: Unquoted service path detection, risky listening port checks (SMB 445, RDP 3389).
* `startup`, `updates`, & `event_logs`: Persistence mechanisms, missing patch detection, bounded 24-hour log traversal.
* `fim`: Cryptographic SHA-256 baseline creation, detection of altered system binaries.
* `registry` & `drivers`: LSA Protection, Credential Guard, vulnerable driver blocklist.
* `ml_anomaly` & `threat_intel`: Anomaly scoring, CrowdStrike Falcon IOC integration and offline dictionary matching.
* `compliance`: Verification of CIS, NIST, ISO 27001, and HIPAA scoring calculations.

### 2. `tests/test_database.py` (Persistence & Dual-Engine Parity)
* Dual SQLite and PostgreSQL DDL schema validation.
* Table creation: `scans`, `findings`, `telemetry_log`, `remediation_log`, `fim_baselines`, `nvd_cve_cache`.
* Automatic Postgres fallback to SQLite on unreachable network nodes.
* High-speed SQL index verification.
* TTL pruning and database maintenance (`maintain_database()`).
* Recursive NUL (0x00) byte sanitization across strings, dicts, and lists.

### 3. `tests/test_remediation.py` (Playbook Safety & Rollback)
* Declarative playbook structure validation in `security/remediation.py`.
* Playbook impact previews (`get_remediation_preview()`).
* Approval gating enforcement for high-risk actions.
* `safe_only_policy` enforcement.
* Reversible rollback command execution and verification.
* Chronological audit log tracking in the `remediation_log` table.

### 4. `tests/test_api.py` (Flask REST API & Middleware)
* Endpoint access: `GET /`, `GET /api/scan/progress`, `GET /api/history`, `GET /api/telemetry`.
* Authentication middleware: `@require_auth` enforcement with `X-Defiant-Key` and `Authorization: Bearer`.
* Concurrency guard: `409 Conflict` response on simultaneous scan requests.
* State lock verification: thread-safe polling without race conditions.
* Mutating endpoints: `POST /api/remediate/preview`, `POST /api/remediate/execute`, `POST /api/remediate/rollback`, `POST /api/fim/reset`, `POST /api/shutdown`.

### 5. `tests/test_audit.py` (Scoring Engine Mathematics)
* Perfect baseline calculation (190/190 points).
* Deduction subtraction per severity level (Critical: -10, High: -5, Medium: -3, Low: -1).
* Mathematical score floor enforcement (guaranteeing category scores cannot go negative).

---

## 26.3 Mocking Strategies (`tests/conftest.py`)

All tests execute fully hermetically without modifying host system state:
* **PowerShell Isolation**: `mock_powershell` monkeypatches `utils.powershell.run_powershell` and `run_powershell_json` to return static mock payloads.
* **WMI Isolation**: `mock_wmi` provides synthetic objects for Windows Management Instrumentation.
* **WinTrust Isolation**: Ctypes function pointers to `wintrust.dll:WinVerifyTrust` are stubbed out to return simulated catalog signatures.
* **Database Isolation**: `in_memory_db` dynamically redirects SQL queries to an isolated in-memory SQLite database (`:memory:`).

---

## 26.4 Running the Test Suite

```powershell
python -m pytest tests/ -v
```

**Results:**
* **61 passing tests** in ~4.3 seconds.
* **100% offline verification.**
