---
last_mapped_commit: f61906e15b5f40f34417ffe3a12a6a7015696188
last_mapped_at: 2026-10-17
---
# Coding Conventions

**Analysis Date:** 2026-10-17

## Naming Patterns

**Files:**
- Python modules: `lowercase_snake_case.py` (e.g. `modules/threat_intel.py`, `modules/ml_anomaly.py`, `security/remediation.py`)
- HTML Templates: `lowercase.html` (e.g. `templates/dashboard.html`, `templates/report.html`)
- Spec/Build files: `PascalCase_SnakeCase.spec` (e.g. `Defiant_Ultimate.spec`)
- Documentation: `PascalCase_With_Underscores.md` or `UPPERCASE.md` (e.g. `documentation/Developer_Guide.md`, `README.md`)

**Functions:**
- Action / Query functions: `snake_case` prefixed by action verb:
  - Data collection: `get_<subsystem>()` (e.g. `get_defender_status()`, `get_listening_ports()`, `get_system_info()`)
  - Evaluation / Analysis: `assess_<subsystem>()` or `audit_<subsystem>()` (e.g. `assess_firewall()`, `audit_fim()`, `audit_anomalies()`)
  - Formatting / Display: `display_<subsystem>()` (e.g. `display_software()`, `display_final_score()`)
  - Execution / Hardening: `execute_<action>()`, `rollback_<action>()`, `get_<action>_preview()`

**Variables & Data Structures:**
- Local variables and parameters: `snake_case` (e.g. `sys_info`, `all_findings`, `progress_tracker`, `category_scores`)
- Global registries and weight mappings: `UPPER_SNAKE_CASE` (e.g. `CATEGORY_WEIGHTS`, `SEVERITY_DEDUCTIONS`, `PLAYBOOKS`, `THREAT_PATTERNS`, `COMPLIANCE_MAPPINGS`)
- Global state holders: `UPPER_SNAKE_CASE` (e.g. `LATEST_SCAN`, `SCAN_PROGRESS`, `DB_ENGINE`)

**Types & Classes:**
- Test Cases and Structs: `PascalCase` (e.g. `TestSecurityPlatform`, `GUID`, `WINTRUST_DATA`, `WINTRUST_FILE_INFO`)

## Code Style

**Formatting:**
- Indentation: 4 spaces per indentation level across all Python source files
- Line breaks and spacing: Standard PEP 8 conventions with blank lines separating logical blocks
- String quotation: Double quotes (`"..."`) preferred for dictionary keys, JSON strings, and API routes; single quotes (`'...'`) common in command strings and SQL statements

**Linting:**
- No formal linter (flake8/ruff/pylint) configuration currently checked into the repository
- Standard PEP 8 clean syntax maintained throughout `modules/`, `security/`, and `database/`

## Import Organization

**Order:**
1. Python Standard Library imports (`os`, `sys`, `json`, `hashlib`, `subprocess`, `urllib.request`, `datetime`, `concurrent.futures`, `ctypes`)
2. Third-Party libraries (`psutil`, `flask`, `flask_cors`, `tabulate`, `colorama`, `numpy`, `sklearn.ensemble`, `psycopg2`)
3. Internal application modules (`modules.*`, `security.*`, `database.*`, `utils.*`)

**Path Aliases:**
- Absolute imports rooted at repository directory (e.g. `from modules.defender import get_defender_status`, `from database.database import init_db`, `from utils.powershell import run_powershell_json`)

## Error Handling

**Patterns:**
- **Defensive Graceful Degradation:** External OS calls (PowerShell, WMI, Win32 APIs) and network queries are isolated in `try...except` blocks to prevent cascading failures.
- **Structured Error Dictionaries:** Helper functions return error payloads rather than raising unhandled exceptions (e.g. `utils/powershell.py:run_powershell_json` returns `{"error": "PowerShell execution failed."}`).
- **Information Findings on Missing Primitives:** When an optional dependency or prerequisite is absent (such as `scikit-learn` in `modules/ml_anomaly.py`), the module appends an `INFO` finding (`id: "ML-ERR"`) explaining the situation rather than halting execution.

```python
try:
    # Attempt system inspection or external API call
    result = perform_query()
except Exception as e:
    # Graceful degradation returning structured fallback finding
    findings.append({
        "id": "SYS-ERR",
        "category": "System",
        "severity": "INFO",
        "title": "Check Incomplete",
        "description": f"Unable to query system subsystem: {str(e)}"
    })
```

## Logging

**Framework:**
- Standard console output via `print()` formatted with `tabulate` and `colorama` for CLI mode (`main.py`)
- Python standard `logging` configured in `utils/logger.py`
- Database-backed transactional audit logging in `database/database.py` (`remediation_log` table)

**Patterns:**
- Console display employs border tables (`tabulate(..., tablefmt="grid")`) and ANSI color headers for readability.
- Remediation operations log timestamp, finding ID, action type (`EXECUTE`/`ROLLBACK`), status (`SUCCESS`/`FAILED`), and message to `remediation_log`.

## Comments & Documentation

**When to Comment:**
- Module headers: File path and high-level component description at top of file (e.g. `modules/threat_intel.py: Threat Intelligence Engine: Correlates local telemetry with IOCs...`)
- Function docstrings: Triple-quoted docstrings defining purpose and parameter expectations
- Complex API bindings: Detailed inline commentary for ctypes structures and Windows API flags (`security/verification.py`)

## Function Design

**Size:**
- Targeted single-responsibility functions generally under 40-60 lines
- Module functions separated cleanly into:
  1. Collection (`get_*`): Retrieves system state
  2. Assessment (`assess_*`): Analyzes state against security rules and emits finding dictionaries
  3. Presentation (`display_*`): Formats output for terminal users

**Return Values:**
- Standardized Finding Schema: Assessment functions return a `list` of finding dictionaries containing `id`, `category`, `severity`, `title`, and `description`.
- Score tuple: `run_full_audit()` returns `(sys_info, score_data, findings, all_module_data)`.

## Module Design

**Exports:**
- Modules expose public getter and assessment functions directly.
- Package `__init__.py` files used in `utils/` and root packages.

---

*Convention analysis: 2026-10-17*
