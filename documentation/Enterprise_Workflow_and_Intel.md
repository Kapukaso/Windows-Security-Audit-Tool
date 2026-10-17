# Enterprise Remediation & Threat Intelligence

This document details the latest enterprise features integrated into the Defiant Security Audit Tool, specifically focusing on the advanced Remediation workflows and the CrowdStrike-powered Threat Intelligence engine.

---

## 1. Advanced Remediation Engine (`security/remediation.py`)

The automated hardening logic was completely overhauled to support enterprise change-management policies. It transitioned from a basic "apply fix" script into a structured, playbook-driven workflow.

### New Workflow Features
* **Execution Previews (`/api/remediate/preview`):** Before applying a fix, the frontend can fetch the precise PowerShell/Subprocess command that will be executed, alongside a strict `SAFE`, `MEDIUM`, or `HIGH` risk rating.
* **Approval Gating (`/api/remediate/execute`):** High-risk actions (like disabling SMBv1) are strictly blocked by the backend unless an explicit `approval_granted=True` flag is passed via the API.
* **Safe-Only Policy Enforcement:** The engine natively supports a `safe_only_policy` flag that completely rejects any playbook not mathematically tagged as `SAFE`.
* **Automated Rollbacks (`/api/remediate/rollback`):** Every remediation playbook is now paired with an inverse rollback command. If a fix breaks a legacy application, a single API call instantly restores the system state.
* **Immutable Audit Logging (`remediation_log` table):** Every successful fix, failed fix, blocked fix, and rollback is permanently recorded in the database (either PostgreSQL or SQLite, depending on the `.env` configuration).

---

## 2. Threat Intelligence Engine (`modules/threat_intel.py`)

The platform now natively scans for active Indicators of Compromise (IOCs) during the audit cycle by cross-referencing live processes, hashes, and sockets against Threat Intelligence feeds.

### Core Capabilities
* **CrowdStrike Falcon Integration:** The `.env` file now supports `FALCON_CLIENT_ID` and `FALCON_CLIENT_SECRET`. If provided, the engine securely authenticates with the CrowdStrike OAuth2 API (`https://api.crowdstrike.com`) and pulls down the latest `malicious_confidence:'high'` hashes and IPs to use during the scan. (If keys are absent, it gracefully falls back to an offline simulated IOC dictionary).
* **Malicious Process Hashing:** Uses `psutil` to iterate over all active executables, calculates their live SHA-256 hashes, and checks them against the CrowdStrike IOCs.
* **Suspicious C2 Sockets:** Checks active network connections established by local processes to see if they are beaconing out to known bad IP addresses.
* **MITRE ATT&CK Command Matching:** Inspects the raw command-line strings (`cmdline`) of all running processes. It uses regex pattern matching to instantly flag advanced evasive techniques like:
  * `certutil.exe -urlcache -split -f` -> **Ingress Tool Transfer (T1105)**
  * `vssadmin delete shadows` -> **Inhibit System Recovery (T1490)**
  * `powershell.exe -EncodedCommand` -> **PowerShell Execution (T1059.001)**

---

## 3. UI/UX Refinements (`templates/dashboard.html`)

The frontend Dashboard was significantly upgraded to match the power of the backend workflows.

* **Tailwind Toast Notifications:** All native, blocking browser `alert()` boxes were purged. The dashboard now uses a dynamic, non-blocking Toast notification system (powered by Tailwind CSS and Lucide Icons) that smoothly slides in from the bottom-right corner to display execution statuses, errors, and approvals.
* **Remediation Approval Modal:** Clicking an "Automated Fix" button now triggers a backdrop-blurred overlay modal. It displays the Target Finding, the Risk Level, the Description, and a live code-block preview of the exact command impact before the user explicitly clicks the "Approve & Execute" button.
