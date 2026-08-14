# Phase 4: Local Users & Identity Management

## 4.1 Academic Overview & Motivation
According to the Principle of Least Privilege (PoLP), users should only possess the minimum permissions necessary to perform their jobs. A massive percentage of malware relies on the logged-in user having Local Administrator privileges to modify registry keys, install rootkits, or disable antivirus software. Phase 4 deeply audits the Local Security Authority (LSA) database to map user accounts and privilege groups.

This aligns with **CIS Control 5: Account Management** and **CIS Control 6: Access Control Management**.

## 4.2 Technical Objectives
1. **Account Enumeration:** Extract a list of all local accounts (ignoring Active Directory accounts for the scope of a local endpoint audit).
2. **Privilege Mapping:** Determine exactly which local accounts belong to the highly sensitive `Administrators` group.
3. **Account Hygiene:** Detect if default legacy accounts (like `Guest` or `DefaultAccount`) are active, as these are common vectors for anonymous or unauthenticated access.
4. **Authentication Integrity:** Identify accounts that do not require a password to log in.

## 4.3 Algorithmic Implementation & Libraries
To interact with the Windows SAM (Security Account Manager) database securely, the platform utilizes Windows Management Instrumentation (WMI) via the third-party `wmi` Python wrapper.

### Step 1: Mapping the Users
The algorithm queries the `Win32_UserAccount` class where `LocalAccount=True`. This returns an object list containing the `Name`, `Disabled`, and `PasswordRequired` attributes.

### Step 2: Mapping the Administrators
The algorithm then queries the `Win32_GroupUser` association class specifically targeting the `Administrators` group. It extracts the username from the `PartComponent` string using regex or string splitting.

```python
import wmi

def get_local_users():
    c = wmi.WMI()
    users = []
    
    # Extract Local Admins
    admins = []
    for group in c.Win32_GroupUser():
        if "Name=\"Administrators\"" in group.GroupComponent:
            # Parse 'PartComponent' string to extract the username
            username = group.PartComponent.split('Name="')[1].split('"')[0]
            admins.append(username)
            
    # Extract User Metadata
    for user in c.Win32_UserAccount(LocalAccount=True):
        users.append({
            "Name": user.Name,
            "IsAdmin": user.Name in admins,
            "Disabled": user.Disabled,
            "PasswordRequired": user.PasswordRequired
        })
    return users
```

## 4.4 Vulnerability Assessment Logic
The risk engine processes the structured user dictionaries against hardcoded identity management rules:

| Finding ID | Trigger Condition | Severity | Justification |
| :--- | :--- | :--- | :--- |
| **USR-001** | `IsAdmin == True` & `Disabled == False` | **CRITICAL** | Active local administrator accounts break PoLP and allow full system compromise if the credentials are stolen. |
| **USR-002** | `Name == 'Guest'` & `Disabled == False` | **HIGH** | The Guest account allows anonymous login and bypasses standard identity attribution. |
| **USR-003** | `PasswordRequired == False` | **MEDIUM** | Blank passwords allow physical or local RDP access without brute-forcing. |

## 4.5 Remediation & Future Expansion
Due to the destructive potential of disabling user accounts (e.g., locking out the only Administrator on a machine), automated remediation for USR-001 is deliberately restricted. Future enterprise versions of this tool could integrate with LAPS (Local Administrator Password Solution) to rotate admin passwords rather than flagging them purely as a vulnerability.
