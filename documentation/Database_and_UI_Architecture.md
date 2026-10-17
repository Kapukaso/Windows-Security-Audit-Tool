# Database Architecture & UI Design

This document details the enterprise dual-engine database architecture, data sanitization protocols, schema migrations, and single-port HUD interface design in the Defiant Windows Security Audit Tool.

---

## 1. Dual-Engine Persistence (`database/database.py`)

The platform supports both standalone local operations and centralized enterprise deployments via a unified database abstraction layer.

### Engine Routing & Dialect Adaptation
* **Environment-Driven Configuration**: Configured via `.env` variables (`DB_ENGINE=sqlite` or `DB_ENGINE=postgres`, with `POSTGRES_URL`).
* **Dynamic Dialect Translation**: Automatically handles dialect variances between SQLite and PostgreSQL:
  * Primary keys: `AUTOINCREMENT` (SQLite) vs `SERIAL` (PostgreSQL).
  * Parameter placeholders: `?` (SQLite) vs `%s` (PostgreSQL).
  * Auto-generated IDs: `cursor.lastrowid` (SQLite) vs `INSERT ... RETURNING id` (PostgreSQL).
* **Automatic Fallback**: If PostgreSQL connection fails or credentials are invalid, the connector logs a warning and falls back safely to local `audit_history.db` SQLite storage.

### Unified Relational Schema

```text
┌────────────────┐       ┌─────────────────┐
│     scans      │1     *│    findings     │
├────────────────┼───────┼─────────────────┤
│ id (PK)        │       │ id (PK)         │
│ timestamp      │       │ scan_id (FK)    │
│ hostname       │       │ finding_id      │
│ total_earned   │       │ category        │
│ total_possible │       │ severity        │
│ percentage     │       │ title           │
└────────────────┘       └─────────────────┘

┌────────────────┐       ┌─────────────────┐
│ telemetry_log  │       │ remediation_log │
├────────────────┼───────┼─────────────────┤
│ id (PK)        │       │ id (PK)         │
│ timestamp      │       │ timestamp       │
│ cpu_percent    │       │ finding_id      │
│ ram_percent    │       │ action_type     │
└────────────────┘       │ status          │
                         │ message         │
                         └─────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  fim_baselines   │     │  nvd_cve_cache   │
├──────────────────┼─────┼──────────────────┤
│ id (PK)          │     │ id (PK)          │
│ file_path (UQ)   │     │ software_name    │
│ sha256_hash      │     │ software_version │
│ timestamp        │     │ cve_data (JSON)  │
└──────────────────┘     │ timestamp        │
                         └──────────────────┘
```

### High-Speed Indexing
To prevent full-table scans across large datasets, explicit indexes are created on startup:
* `idx_findings_scan_id` on `findings(scan_id)`
* `idx_findings_severity` on `findings(severity)`
* `idx_telemetry_timestamp` on `telemetry_log(timestamp)`
* `idx_fim_path` on `fim_baselines(file_path)`
* `idx_cve_lookup` on `nvd_cve_cache(software_name, software_version)`

---

## 2. NUL (0x00) Byte Sanitization Protocol

Windows system APIs (PowerShell, WMI, Win32 registry APIs, driver inspection) frequently output strings containing embedded NUL (`0x00`) characters due to C-style null-terminated wide-character buffers (`wchar_t`).

Standard PostgreSQL drivers (`psycopg2`) and strict UTF-8 decoders reject strings containing `\x00` with the fatal error:
```text
A string literal cannot contain NUL (0x00) characters.
```

### Sanitization Implementation
`database/database.py` and `utils/powershell.py` enforce recursive sanitization across all data boundaries:

```python
def sanitize_null_bytes(val):
    """Recursively removes NUL (0x00) bytes from strings, dicts, and lists."""
    if isinstance(val, str):
        return val.replace("\x00", "")
    elif isinstance(val, dict):
        return {sanitize_null_bytes(k): sanitize_null_bytes(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_null_bytes(item) for item in val]
    return val
```

This ensures that registry binary values, driver certificates, and raw PowerShell JSON outputs are completely cleansed before SQL execution or JSON deserialization.

---

## 3. Data Retention & Maintenance (`maintain_database`)

At the conclusion of each security audit, `maintain_database()` automatically executes pruning routines:
1. **Telemetry Purging**: Deletes telemetry rows older than 7 days.
2. **Scan History Capping**: Retains the top 100 scans, pruning older scan records.
3. **Cascading Finding Cleanup**: Deletes orphaned `findings` rows whose parent `scan_id` was purged.
4. **CVE Cache Eviction**: Drops cached NVD CVE entries older than 30 days to ensure vulnerability data remains fresh.

---

## 4. Single-Port HUD Interface (`templates/dashboard.html`)

The frontend operates as a unified, single-port interface hosted directly on the Flask server (`http://127.0.0.1:5000`).

### Key UI Capabilities
* **Single-Port Architecture**: Eliminates redundant Node.js proxy servers; all static assets, templates, and REST APIs are served from port 5000.
* **State Synchronization**: Backend state variables (`SCAN_PROGRESS`, `LATEST_SCAN`) are protected by `threading.Lock` to ensure smooth concurrent polling without UI stutter or data corruption.
* **Sci-Fi HUD Theme**: Styled with Tailwind CSS, custom geometric clip paths (`clip-hud`, `clip-btn`), and Lucide icons.
* **Live Telemetry Stream**: Real-time canvas chart visualizing CPU and RAM consumption every 2 seconds.
* **Two-Step Remediation Modal**: Preview modal displays playbook details, exact PowerShell commands, and approval toggles before executing hardening changes.
* **Toast Notification Engine**: Non-blocking slide-in alerts replacing intrusive native browser popups.
