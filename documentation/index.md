# Defiant: Windows Security Posture Platform Documentation

Welcome to the documentation for **Defiant**, an enterprise-grade Endpoint Detection and Security Audit platform.

This `/documentation` directory contains a detailed, phase-by-phase academic and technical breakdown of the platform's architecture, as well as the mapping to general security rubrics.

## Table of Contents

### 1. Platform Architecture & Developer Guides
* [API Reference](API_Reference.md) - Details the Flask REST API endpoints used by the dashboard.
* [Developer Guide](Developer_Guide.md) - Guide for extending the platform and adding new audit modules.
* [Rubric Mapping](Rubric_Mapping.md) - Maps the platform's features to an 11-point security rubric.

### 2. Audit Modules (Phases 1-10)
These phases represent the core data collection and assessment modules located in the `modules/` directory.

* [Phase 1: System Information](Phase_01_System_Information.md)
* [Phase 2: Microsoft Defender](Phase_02_Defender_Status.md)
* [Phase 3: Windows Firewall](Phase_03_Firewall_Status.md)
* [Phase 4: Local Users](Phase_04_Local_Users.md)
* [Phase 5: Installed Software](Phase_05_Installed_Software.md)
* [Phase 6: Running Services](Phase_06_Running_Services.md)
* [Phase 7: Startup Applications](Phase_07_Startup_Applications.md)
* [Phase 8: Network Ports](Phase_08_Network_Ports.md)
* [Phase 9: Password Policy](Phase_09_Password_Policy.md)
* [Phase 10: Updates & Logs](Phase_10_Updates_and_Logs.md)

### 3. Core Engines & Interfaces (Phases 11-21)
These phases cover the analytical, persistence, UI, testing, and advanced security mechanisms of the platform.

* [Phase 11: Risk Scoring Engine](Phase_11_Scoring_Engine.md) - The math behind the 135-point security score (`modules/score.py`).
* [Phase 12: Reporting](Phase_12_Reporting.md) - JSON and HTML report generation.
* [Phase 13: Database Persistence](Phase_13_Database.md) - SQLite historical tracking.
* [Phase 14: Web Dashboard](Phase_14_Web_Dashboard.md) - The Flask-based single page application (SPA).
* [Phase 15: Remediation Engine](Phase_15_Remediation.md) - Automated hardening actions (`security/remediation.py`).
* [Phase 16: Automated Testing](Phase_16_Testing.md) - Unit testing for the scoring model.
* [Phase 17: Machine Learning](Phase_17_Machine_Learning.md) - ML-based anomaly detection (`modules/ml_anomaly.py`).
* [Phase 18: File Integrity Monitoring](Phase_18_File_Integrity_Monitoring.md) - Detects unauthorized modifications (`modules/fim.py`).
* [Phase 19: Deployment](Phase_19_Deployment.md) - Deployment and packaging guides.
* [Phase 20: CVE Lookup](Phase_20_CVE_Lookup.md) - NIST NVD vulnerability lookup for software (`modules/cve_lookup.py`).
* [Phase 21: Registry Security](Phase_21_Registry_Security.md) - Audits critical Windows Registry configurations (`modules/registry.py`).
<<<<<<< Updated upstream
* [Phase 22: Frontend HUD Upgrade](Phase_22_Frontend_HUD_Upgrade.md) - Rebuilding the UI into a Sci-Fi HUD using Tailwind CSS.
* [Phase 23: Advanced Remediation & CVE Upgrades](Phase_23_Advanced_Remediation_and_CVE_Upgrades.md) - Winget integration, Playbook Modals, UI Caching, and NIST API persistence.
* [Phase 24: Concurrency & Utilities](Phase_24_Concurrency_and_Utilities.md) - Asynchronous multi-threading for data collection and standardized OS utilities.
=======
>>>>>>> Stashed changes

## System Workflow Diagram

1. **Initiation:** The user triggers a scan via the Dashboard (Phase 14) or CLI (`main.py`).
2. **Collection & Assessment (Phases 1-10):** The `modules/` layer runs parallel or sequential checks against WMI, PowerShell, and the Registry.
3. **Scoring (Phase 11):** Findings are aggregated and passed to `modules/score.py` to deduct points based on severity.
4. **Persistence (Phase 13):** The final payload (system info, score, findings) is saved to `audit_history.db`.
5. **Presentation:** The JSON is served to the frontend or rendered into CLI tables/HTML reports.
6. **Remediation (Phase 15):** The user can trigger automated fixes for specific finding IDs via the `/api/remediate` endpoint.
