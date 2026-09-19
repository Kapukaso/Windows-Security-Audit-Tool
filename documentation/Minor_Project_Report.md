# Minor Project Report: Windows Security Posture Platform (Defiant)

## 1. Abstract
The **Windows Security Posture Platform (Defiant)** is a comprehensive endpoint security auditing and remediation tool. Traditionally, analyzing a Windows machine for security misconfigurations requires manual command-line checks or expensive enterprise software. This project automates the auditing process by analyzing system configurations, calculating a mathematical risk score, and presenting the telemetry on a modern web dashboard. It also features a "Do No Harm" automated remediation engine to instantly fix critical vulnerabilities.

## 2. Introduction

### 2.1 Problem Statement
Operating systems often come with default configurations that favor usability over security. Users and administrators frequently overlook critical security settings such as weak password policies, exposed network ports, disabled firewalls, or legacy protocols. Manually checking these configurations is time-consuming and error-prone, leading to compromised endpoints.

### 2.2 Project Objectives
1. **Automated Auditing:** To programmatically scan the host system across 10 security domains (Firewall, Defender, Users, Ports, Services, etc.) without requiring heavy third-party agents.
2. **Risk Quantification:** To implement a mathematical scoring engine that evaluates vulnerabilities based on severity and assigns an overall health score (out of 135 points).
3. **Actionable Interface:** To build a user-friendly, web-based dashboard for visualizing the security posture and live hardware telemetry.
4. **Automated Hardening:** To provide 1-click remediation scripts that automatically fix specific vulnerabilities without risking system stability.

## 3. Technology Stack
This project is built using a diverse, full-stack architecture:

* **Backend Server & API:** Python 3, Flask Micro-framework
* **System Introspection:** `psutil`, Windows Management Instrumentation (WMI), Subprocess (PowerShell execution), `socket`
* **Database:** SQLite3 (Local persistence)
* **Frontend Dashboard:** HTML5, CSS3, Vanilla JavaScript (Fetch API for asynchronous REST calls)

## 4. System Architecture
The platform operates on a modular, multi-tier architecture to ensure separation of concerns:

1. **Data Collection Layer (`modules/`):** A collection of decoupled Python scripts that extract raw operating system data (e.g., active listening ports, installed software, Windows Defender status).
2. **Scoring & Analysis Layer (`modules/score.py`):** Validates the raw data against security baselines. It applies severity deductions (Critical = -10 points, High = -5 points) against category weights to generate the final percentage.
3. **Persistence Layer (`database/database.py`):** Stores relational scan history and findings into an SQLite database (`audit_history.db`), enabling administrators to track compliance over time.
4. **Presentation & API Layer (`app.py`):** A Flask application exposing RESTful JSON endpoints (`/api/scan`, `/api/history`, `/api/telemetry`). The frontend consumes these endpoints dynamically to render charts and findings without page reloads.

## 5. Key Modules Implemented

* **User Account Security:** Hunts for unauthorized accounts in the Local Administrators group and audits the OS password length and lockout policies to defend against brute-forcing.
* **Network & Port Security:** Maps every active `LISTEN` socket on the machine, flagging dangerous legacy protocols (e.g., SMBv1, Telnet).
* **Malware Protection Verification:** Verifies that Microsoft Defender's Real-Time Protection and Behavior Monitoring are actively running, not just installed.
* **Automated Remediation Engine:** A Python module that executes safe PowerShell commands to fix specific findings (e.g., automatically enforcing a minimum password length of 8 characters).

## 6. Conclusion
The Windows Security Posture Platform successfully automates the complex task of endpoint security auditing. By combining system-level scripting with a modern web stack, the project bridges the gap between raw command-line data and actionable security intelligence. It demonstrates proficiency in full-stack development, operating system interaction, and cybersecurity principles.

## 7. Future Scope
* **Cloud Integration (Database):** Migrating from local SQLite to a cloud database (like Supabase PostgreSQL) to enable centralized fleet management for multiple endpoints.
* **Authentication:** Implementing session-based login on the dashboard to restrict access to authorized administrators.
* **PDF Export:** Adding functionality to generate and download professional PDF compliance reports for management review.
