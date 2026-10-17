# Defiant: Windows Security Posture Platform Documentation

Welcome to the documentation for **Defiant**, an enterprise-grade Endpoint Detection, Security Audit, and Automated Remediation platform for Microsoft Windows.

This `/documentation` directory contains a detailed, phase-by-phase academic and technical breakdown of the platform's architecture, as well as the mapping to general security rubrics.

## Table of Contents

### 1. Platform Architecture & Developer Guides
* [API Reference](API_Reference.md) - Details the Flask REST API endpoints, token authentication (`@require_auth`), and JSON payloads.
* [Developer Guide](Developer_Guide.md) - Guide for extending the platform, adding new audit collectors, declarative playbooks, and mock tests.
* [Database & UI Architecture](Database_and_UI_Architecture.md) - Dual-engine persistence (SQLite / PostgreSQL), SQL indexing, retention pruning, and single-port HUD interface.
* [Enterprise Workflow & Threat Intel](Enterprise_Workflow_and_Intel.md) - Two-step remediation with rollback, CrowdStrike Falcon IOC feed, and MITRE ATT&CK technique mapping.
* [Rubric Mapping](Rubric_Mapping.md) - Maps the platform's features to an 11-point security rubric.

### 2. Audit Modules (Phases 1-10)
These phases represent the core data collection and assessment modules located in the `modules/` directory.

* [Phase 1: System Information](Phase_01_System_Information.md) - Collects OS version, hardware specs, uptime, and identity.
* [Phase 2: Microsoft Defender](Phase_02_Defender_Status.md) - Checks real-time protection, signature ages, and engine health.
* [Phase 3: Windows Firewall](Phase_03_Firewall_Status.md) - Audits Domain, Private, and Public firewall profiles.
* [Phase 4: Local Users](Phase_04_Local_Users.md) - Audits administrator group members, guest account state, and inactive users.
* [Phase 5: Installed Software](Phase_05_Installed_Software.md) - Enumerates 32-bit and 64-bit software from uninstall registry keys.
* [Phase 6: Running Services](Phase_06_Running_Services.md) - Checks unquoted service paths and vulnerable background services.
* [Phase 7: Startup Applications](Phase_07_Startup_Applications.md) - Audits Run keys and startup directory persistence mechanisms.
* [Phase 8: Network Ports](Phase_08_Network_Ports.md) - Checks open listening TCP/UDP ports and exposed risky services (RDP, SMB).
* [Phase 9: Password Policy](Phase_09_Password_Policy.md) - Audits complexity, minimum length, lockout thresholds, and NTLMv2 enforcement.
* [Phase 10: Updates & Logs](Phase_10_Updates_and_Logs.md) - Checks missing security updates and recent Security Event Log anomalies.

### 3. Core Engines, Persistence, & Advanced Capabilities (Phases 11-26)
These phases cover the analytical, persistence, UI, testing, and advanced security mechanisms of the platform.

* [Phase 11: Risk Scoring Engine](Phase_11_Scoring_Engine.md) - The math behind the 190-point weighted security score across 13 categories (`modules/score.py`).
* [Phase 12: Reporting](Phase_12_Reporting.md) - JSON and standalone styled HTML report generation (`modules/report.py`).
* [Phase 13: Database Persistence](Phase_13_Database.md) - Dual-engine SQLite & PostgreSQL persistence, schema migrations, and TTL maintenance.
* [Phase 14: Web Dashboard](Phase_14_Web_Dashboard.md) - The Flask-based single-port HUD application (`templates/dashboard.html`).
* [Phase 15: Remediation Engine](Phase_15_Remediation.md) - Automated hardening actions, preview impact analysis, and reversible rollback (`security/remediation.py`).
* [Phase 16: Automated Testing](Phase_16_Testing.md) - Unit testing for scoring algorithms and mock isolation.
* [Phase 17: Machine Learning](Phase_17_Machine_Learning.md) - Isolation Forest ML anomaly detection on system telemetry (`modules/ml_anomaly.py`).
* [Phase 18: File Integrity Monitoring](Phase_18_File_Integrity_Monitoring.md) - SHA-256 baseline tracking for critical Windows system files (`modules/fim.py`).
* [Phase 19: Deployment](Phase_19_Deployment.md) - Deployment and packaging guides for production enterprise nodes.
* [Phase 20: CVE Lookup](Phase_20_CVE_Lookup.md) - NIST NVD vulnerability lookup with persistent local SQLite/PostgreSQL caching and circuit breaker (`modules/cve_lookup.py`).
* [Phase 21: Registry Security](Phase_21_Registry_Security.md) - Deep kernel & registry hardening: LSA Protection, Credential Guard, and UAC controls (`modules/registry.py`).
* [Phase 22: Frontend HUD Upgrade](Phase_22_Frontend_HUD_Upgrade.md) - Single-port Sci-Fi HUD design using Tailwind CSS and Lucide icons.
* [Phase 23: Advanced Remediation & CVE Upgrades](Phase_23_Advanced_Remediation_and_CVE_Upgrades.md) - Winget integration, Playbook Modals, UI Caching, and NIST API persistence.
* [Phase 24: Concurrency & Utilities](Phase_24_Concurrency_and_Utilities.md) - Multi-threaded `ThreadPoolExecutor` audit orchestration and safe PowerShell execution.
* [Phase 25: Multi-Standard Compliance Engine](Phase_25_Multi_Standard_Compliance.md) - Automated control mapping against CIS Benchmarks, NIST SP 800-53, ISO/IEC 27001, and HIPAA Security Rule (`modules/compliance.py`).
* [Phase 26: Automated Unit & Mock Test Suite](Phase_26_Automated_Unit_and_Mock_Test_Suite.md) - Comprehensive 61-test Pytest suite with hermetic mocks for WMI, PowerShell, and WinTrust ctypes (`tests/`).

## System Workflow Architecture

```text
[Browser HUD Client / REST API]
          │
          │ (POST /api/scan, Bearer / X-Defiant-Key Auth)
          ▼
   [Flask Server (app.py)]
          │
          ▼
  [Audit Orchestrator (main.py)]
          │ (ThreadPoolExecutor - 10 Workers)
          ├──► System Info & Users
          ├──► Defender & Firewall
          ├──► Services, Startup & Ports
          ├──► Password Policy & Updates
          ├──► Registry & Drivers (LSA, Credential Guard)
          ├──► File Integrity Monitoring (FIM SHA-256)
          ├──► ML Telemetry Anomalies
          ├──► Threat Intel (CrowdStrike Falcon / Offline IOCs)
          └──► Software Inventory & Local NVD CVE Cache
          │
          ▼
   [Compliance & Scoring Engines]
          ├──► Risk Score (190 Points Max across 13 Categories)
          └──► Multi-Standard Compliance Report (CIS, NIST, ISO 27001, HIPAA)
          │
          ▼
   [Dual-Engine Persistence (database/database.py)]
          ├──► SQLite (Local Development)
          └──► PostgreSQL (Enterprise Fleet Deployment)
          │
          ▼
   [Two-Step Reversible Remediation (security/remediation.py)]
          ├──► Impact Preview (/api/remediate/preview)
          ├──► Approval Gating & Safe-Only Enforcement (/api/remediate/execute)
          └──► Instant State Rollback (/api/remediate/rollback)
```
