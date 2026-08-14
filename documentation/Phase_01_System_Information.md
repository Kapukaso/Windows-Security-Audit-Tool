# Phase 1: System Information & Environmental Telemetry

## 1.1 Academic Overview & Motivation
In the domain of Endpoint Detection and Response (EDR), context is as critical as the telemetry itself. A vulnerability classified as "High" on a standard user workstation may be reclassified as "Critical" if the system is identified as a mission-critical domain controller. Phase 1 of the Defiant Platform establishes this environmental baseline. Before any security assertions can be made, the system must accurately map the hardware capabilities, operating system kernel version, and network identity of the endpoint. 

This phase aligns with **CIS Control 1: Inventory and Control of Enterprise Assets**, which mandates that organizations actively manage all hardware devices on the network so only authorized devices are given access.

## 1.2 Technical Objectives
1. **Network Attribution:** Extract the `Hostname` and local `IP Address` to uniquely identify the machine within the SQLite audit database.
2. **OS Fingerprinting:** Determine the OS version and release build. This is critical for identifying endpoints running end-of-life (EOL) operating systems (e.g., Windows 7 or older Windows 10 builds) which are no longer receiving security patches.
3. **Hardware Utilization:** Capture CPU and RAM allocation. High CPU utilization during a baseline state can be an Indicator of Compromise (IoC), such as a cryptojacking payload or unauthorized background exfiltration.
4. **Temporal Context:** Record the exact boot time to detect systems that have avoided required security patch reboots.

## 1.3 Algorithmic Implementation & Libraries
The implementation heavily favors cross-platform, low-overhead native libraries to avoid alerting host-based intrusion detection systems (HIDS). 

- `socket.gethostname()` and `socket.gethostbyname()` are used for zero-overhead network resolution.
- `platform.system()`, `platform.release()`, and `platform.version()` access the NT Kernel metadata.
- `psutil` (Python System and Process Utilities) is invoked for hardware metrics. `psutil` wraps native Windows APIs (like `GetSystemInfo` and `GlobalMemoryStatusEx`) via C-extensions, making it highly performant.

### Core Execution Block
```python
import platform, socket, psutil, getpass
from datetime import datetime

def get_system_info():
    memory = psutil.virtual_memory()
    return {
        "Computer Name": socket.gethostname(),
        "Current User": getpass.getuser(),
        "Operating System": f"{platform.system()} {platform.release()}",
        "OS Version": platform.version(),
        "RAM (GB)": round(memory.total / (1024 ** 3), 2),
        "CPU Cores": psutil.cpu_count(logical=False),
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    }
```

## 1.4 Data Structure Output
The module returns a strictly typed Python dictionary. This data structure is deliberately flat to allow O(1) key-value lookups when the data is eventually piped into the Jinja2 HTML reporting template (Phase 12) and the REST API JSON response (Phase 14).

## 1.5 Edge Cases Handled
- **Virtual Machines:** The `psutil` library gracefully handles virtualized CPU cores in Hyper-V or VMware environments without throwing exceptions.
- **Privilege Limitations:** None of the calls in Phase 1 require `NT AUTHORITY\SYSTEM` or Administrator privileges, ensuring the module never crashes during a low-privileged execution context.
