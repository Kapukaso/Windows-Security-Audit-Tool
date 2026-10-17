# Defiant (Windows Security Audit Tool)

## What This Is

Defiant is a lightweight, extensible Windows security posture assessment and hardening platform. It conducts concurrent evaluations across 13 security categories (Defender, Firewall, Users, Password Policy, Updates, Services, Startup, Ports, Event Logs, Software/CVEs, Registry, File Integrity Monitoring, and ML Anomalies), calculates a weighted score out of 190 points, maps findings to major compliance frameworks (CIS, NIST, STIG, ISO 27001, HIPAA, PCI DSS), and provides a web dashboard with reversible hardening playbooks.

## Core Value

Provide reliable, safe, high-speed Windows security auditing and reversible hardening with zero unhandled stalls, consistent multi-database persistence, and bulletproof test coverage.

## Requirements

### Validated

- ✓ 13-category posture auditing & scoring up to 190 points — existing
- ✓ ThreadPoolExecutor concurrent audit execution across 16 tasks — existing
- ✓ Hardening playbook engine with preview, execution, and rollback — existing
- ✓ Native Authenticode WinVerifyTrust signature validation — existing
- ✓ Regulatory compliance cross-referencing (CIS, NIST, STIG, ISO 27001, HIPAA, PCI DSS) — existing
- ✓ Dual database connector architecture for SQLite and PostgreSQL — existing
- ✓ System telemetry streaming and IsolationForest anomaly detection — existing

### Active

- [ ] Clean up and pin dependencies in `requirements.txt` (pin versions and migrate to `psycopg2-binary` for clean Windows builds)
- [ ] Eliminate dual-engine database abstraction leaks in `modules/fim.py` and `app.py` by routing all database operations through `database/database.py:get_connection()`
- [ ] Add thread-safety synchronization to Flask scan state (`SCAN_PROGRESS` and `LATEST_SCAN`) in `app.py`
- [ ] Optimize NIST NVD CVE lookup with local persistence caching, graceful timeouts, and non-blocking asynchronous enrichment
- [ ] Bound Windows Security Event Log scanning with configurable time/count limits to eliminate CPU/IO spikes
- [ ] Secure remediation API endpoints (`/api/remediate/execute`) with local shared secret / API key authentication in `.env`
- [ ] Remove hardcoded sample NVD API key from `.defiant_config.json` and migrate configuration strictly to `.env`
- [ ] Deprecate and remove redundant `node_frontend` static server, consolidating exclusively on Flask Jinja2 HUD
- [ ] Build comprehensive automated unit and mock test suite across all 16 collectors, remediation engine, database, and Flask API routes

### Out of Scope

- Distributed multi-host fleet agent management (server/agent architecture) — deferred to future enterprise milestone
- Complete UI rewrite to a single-page React/Vue application — consolidating on Flask Jinja2 dashboard instead

## Context

- Brownfield codebase running on Windows 10/11 with Python 3.10+
- Historical phases 1–24 implemented the core scanning features, initial UI, and early playbooks
- Codebase mapping documented architecture, stack, testing, and technical debt in `.planning/codebase/CONCERNS.md`
- Primary focus of this milestone is full remediation of all architectural leaks, security vulnerabilities, performance bottlenecks, and test coverage gaps

## Constraints

- **Platform**: Windows 10/11 x64 (uses Windows APIs, PowerShell MpPreference/AdvFirewall, ctypes WinVerifyTrust)
- **Privileges**: Administrator privileges required for deep audit inspection and remediation execution
- **Stack**: Python 3.10+, Flask, SQLite/PostgreSQL (`psycopg2-binary`)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Consolidate on Flask Jinja2; deprecate `node_frontend` | Eliminates duplicated UI maintenance and dual-port server complexity | — Pending |
| Secure `/api/remediate/execute` via local secret/token | Prevents unauthorized local processes from triggering elevated hardening actions | — Pending |
| Implement local caching for NIST NVD queries | Prevents scan stalls and rate-limiting blocks during full system scans | — Pending |
| Build comprehensive mock & unit test suite | Closes the critical gap where only scoring was tested, ensuring collectors and remediations are reliable | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-17 after initialization*
