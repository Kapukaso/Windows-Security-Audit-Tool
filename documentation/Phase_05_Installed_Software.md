# Phase 5: Installed Software & CVE Vectors

## 5.1 Academic Overview & Motivation
Exploitation of vulnerable third-party software (e.g., outdated browsers, PDF readers, and Java runtimes) accounts for a vast majority of initial access vectors used by Advanced Persistent Threats (APTs). Phase 5 focuses on application inventorying to identify high-risk software families that historically suffer from severe Common Vulnerabilities and Exposures (CVEs).

This aligns with **CIS Control 2: Inventory and Control of Software Assets**.

## 5.2 Technical Implementation
Extracting a complete software inventory on Windows is complex because there is no single unified API. The most reliable method is iterating through the `Uninstall` keys in the Windows Registry.

The module queries two primary locations using PowerShell:
1. `HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*` (64-bit software)
2. `HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*` (32-bit software)

It extracts the `DisplayName` and `DisplayVersion` properties, compiling them into a Python list of dictionaries.

## 5.3 Vulnerability Logic
The engine cross-references the inventory against a hardcoded `RISKY_SOFTWARE` dictionary.
- **HIGH (SOFT-001):** Applications like "Java 8", "Adobe Flash", or "Silverlight". These are end-of-life frameworks with unpatchable remote code execution (RCE) vulnerabilities.
- **MEDIUM (SOFT-002):** Applications like "uTorrent" or unapproved Remote Desktop software (e.g., "AnyDesk", "TeamViewer"), which are common vectors for ransomware operators to bypass firewalls.
