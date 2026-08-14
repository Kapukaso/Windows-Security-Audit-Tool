# Phase 6: Running Services & Privilege Escalation

## 6.1 Academic Overview & Motivation
Windows Services operate autonomously in the background, typically running under the highly privileged `NT AUTHORITY\SYSTEM` account. Misconfigurations in how these services are installed lead to local privilege escalation (LPE). The most famous example is the **Unquoted Service Path** vulnerability. 

## 6.2 The Unquoted Service Path Vulnerability
If a service is registered with a path containing spaces, such as `C:\Program Files\My App\service.exe`, but lacks surrounding quotation marks, the Windows API (`CreateProcess`) attempts to execute the path sequentially at every space:
1. `C:\Program.exe`
2. `C:\Program Files\My.exe`
3. `C:\Program Files\My App\service.exe`

If a standard user drops a malicious payload named `Program.exe` into the C: drive, the service will execute the malware as SYSTEM upon reboot.

## 6.3 Technical Implementation
The module queries the WMI `Win32_Service` class to extract the `PathName` and `State` of all running services.

```python
import wmi
c = wmi.WMI()
for service in c.Win32_Service(State="Running"):
    path = str(service.PathName)
    # Detection Algorithm:
    if " " in path and not path.startswith('"'):
        flag_vulnerability("CRITICAL", service.Name)
```
- **CRITICAL (SVC-001):** Any running service with an unquoted service path.
