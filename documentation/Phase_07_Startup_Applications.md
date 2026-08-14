# Phase 7: Startup Applications & Persistence

## 7.1 Academic Overview & Motivation
Once malware infects a machine, its primary goal is to achieve "persistence"—ensuring the payload survives a system reboot. The most common persistence mechanism used by script-kiddies and APTs alike is hooking into the Windows `Run` registry keys.

## 7.2 Technical Objectives
Identify all binaries configured to launch automatically at boot or user login, and flag binaries running from highly suspicious, user-writable directories.

## 7.3 Algorithmic Implementation
The module queries the primary persistence keys:
- `HKCU:\Software\Microsoft\Windows\CurrentVersion\Run` (Executes for the current user)
- `HKLM:\Software\Microsoft\Windows\CurrentVersion\Run` (Executes for all users)

### Detection Logic
Malware rarely installs itself into `C:\Program Files` because it requires UAC (User Account Control) Administrator approval. Instead, it drops payloads into user-writable directories.

| Finding ID | Trigger Condition | Severity |
| :--- | :--- | :--- |
| **START-001** | Path contains `\AppData\Local\Temp` or `\ProgramData` | **HIGH** |
| **START-002** | Path executes directly from the `C:\Users\` root | **MEDIUM** |
