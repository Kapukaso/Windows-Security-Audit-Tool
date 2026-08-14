# Phase 3: Windows Firewall Profiling & Network Boundaries

## 3.1 Academic Overview & Motivation
A properly configured host-based firewall is essential for minimizing an endpoint's network attack surface. In enterprise breaches, initial access is rarely the final goal; threat actors rely on lateral movement (e.g., using SMB or WMI) to traverse the network. Phase 3 evaluates the Windows Filtering Platform (WFP) to ensure that the firewall is actively blocking unauthorized inbound connections across all network profiles.

This phase directly supports **CIS Control 9: Email and Web Browser Protections** (restricting unauthorized network traffic) and **NIST SP 800-53 SC-7 Boundary Protection**.

## 3.2 Technical Objectives
Windows classifies network connections into three distinct profiles:
1. **Domain Profile:** Applied when the endpoint is connected to an Active Directory domain.
2. **Private Profile:** Applied on trusted local networks (e.g., home networks).
3. **Public Profile:** Applied on untrusted networks (e.g., airports, coffee shops).

The objective is to programmatically guarantee that the firewall is enforcing strict inbound blocking on **all three profiles**.

## 3.3 Algorithmic Implementation & Libraries
While PowerShell's `Get-NetFirewallProfile` is modern, it requires specific PowerShell modules that may not be available on legacy systems or stripped-down Windows versions. To ensure maximum compatibility, the platform utilizes the legacy network shell utility: `netsh`.

The command executed is: `netsh advfirewall show allprofiles`

### String Parsing Algorithm
Because `netsh` does not output JSON or XML, the Python module implements a custom string parsing algorithm. It splits the `stdout` by the word "Profile" to create chunks, and then uses string searching to extract the state (ON/OFF).

```python
import subprocess

def get_firewall_status():
    cmd = ["netsh", "advfirewall", "show", "allprofiles"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout
    
    profiles = {"Domain": False, "Private": False, "Public": False}
    
    # Custom parser logic
    sections = output.split("Profile Settings:")
    for section in sections:
        if "Domain Profile" in section:
            profiles["Domain"] = "State\t\t\t\t\t\t\t\tON" in section.replace(" ", "")
        # ... logic repeated for Private and Public
    return profiles
```

## 3.4 Vulnerability Assessment Logic
Firewall configurations operate on a zero-tolerance policy within this platform. If any profile is disabled, the system is exposed.

| Finding ID | Trigger Condition | Severity | Justification |
| :--- | :--- | :--- | :--- |
| **FW-001** | `Domain Profile == OFF` | **CRITICAL** | Endpoint is highly vulnerable to Active Directory lateral movement (e.g., Pass-the-Hash). |
| **FW-002** | `Private Profile == OFF` | **CRITICAL** | Endpoint is vulnerable to local network scanning and exploitation. |
| **FW-003** | `Public Profile == OFF` | **CRITICAL** | Imminent threat. Endpoint is exposed to untrusted peers on public Wi-Fi. |

## 3.5 Edge Cases & Limitations
Currently, the module audits the macro-state of the firewall profiles. It does not iterate through individual port exceptions (e.g., checking if Port 3389 is globally open in the advanced ruleset). To compensate for this limitation, Phase 8 (Network Ports) is implemented later in the pipeline to audit actual active listening sockets, bridging the gap between theoretical firewall rules and active network exposure.
