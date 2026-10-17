# Phase 16: Automated Testing & Reliability

## 16.1 Academic & Architectural Overview
In an enterprise endpoint security tool, pushing broken code or regressions to production endpoints can disrupt critical host operations. Phase 16 establishes a hermetic, mock-driven automated testing framework ensuring that:
1. Scoring algorithms calculate mathematical floors and deductions accurately without score bleed.
2. Collection modules gracefully handle missing services, corrupted registry values, or disabled features without crashing.
3. Database persistence routines maintain schema parity across SQLite and PostgreSQL.
4. Host-mutating remediations enforce strict admin approval and safe rollback.

## 16.2 Modern Testing Framework (Pytest Harness)
The platform transitioned from minimal `unittest` checks to a comprehensive test suite using `pytest`, `pytest-cov`, and `pytest-qt`.

### Test Architecture (`tests/`)

```text
tests/
├── conftest.py             # Global hermetic fixtures (in-memory DB, WMI/PowerShell mocks)
├── test_api.py             # Web API routes, authentication tokens, concurrency locks
├── test_audit.py           # Mathematical risk scoring bounds, floors, and deductions
├── test_audit_modules.py   # Full collector coverage (compliant, findings, error fallbacks)
├── test_database.py        # SQLite/PostgreSQL schema parity, indexing, NUL sanitization
└── test_remediation.py     # Playbook previews, approval gating, and safe rollback
```

### Hermetic Mock Fixtures (`tests/conftest.py`)
To enable tests to run on any developer machine or continuous integration (CI) pipeline without Windows Administrator elevation:
* **`in_memory_db`**: Injects an isolated `:memory:` SQLite connection into `database/database.py` for each test, ensuring no state leakage between test cases.
* **`mock_powershell`**: Intercepts `utils.powershell.run_powershell` and `run_powershell_json`, returning deterministic JSON structures for Defender, firewall profiles, and registry checks.
* **`mock_wmi`**: Mocks the Windows Management Instrumentation (WMI) subsystem to simulate service states and user accounts.
* **`mock_wintrust`**: Stubs out native `wintrust.dll` ctypes calls, allowing Authenticode signature tests to execute rapidly without disk I/O.

## 16.3 Execution & Verification

Run the complete test suite:

```powershell
python -m pytest tests/ -v
```

**Verification Results:**
* **61 passing tests** across 5 test suites.
* **Execution time:** ~4.3 seconds.
* **Zero elevation requirement:** Tests run safely under standard non-privileged user accounts.
