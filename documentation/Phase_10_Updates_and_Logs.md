# Phase 10: Updates and Event Logs

## 10.1 Academic Overview
Security is a continuous lifecycle. A system patched yesterday may be vulnerable today. Phase 10 ensures the Windows Update service is functional and that the OS is actively generating forensic data in the Security Event Log.

## 10.2 Technical Implementation
**1. Patch Management:** 
Queries WMI `Win32_QuickFixEngineering` to retrieve the list of installed Hotfixes (KBs). It parses the `InstalledOn` date strings into Python `datetime` objects and calculates the delta from today's date.
- **HIGH (UPD-001):** Latest security patch is > 30 days old.

**2. Audit Logging:**
Executes PowerShell `Get-EventLog -LogName Security -Newest 1` to verify the log is accessible.
- **HIGH (LOG-001):** Access Denied or log missing. Without logs, Security Information and Event Management (SIEM) tools cannot function, rendering the system completely opaque to incident responders.
