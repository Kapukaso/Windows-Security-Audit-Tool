# Phase 18: File Integrity Monitoring (FIM)

## 18.1 Academic Overview & Motivation
Advanced Persistent Threats (APTs) and rootkits often replace or tamper with critical system binaries to maintain persistence or redirect network traffic. Phase 18 introduces File Integrity Monitoring (FIM), which uses cryptographic hashing to detect unauthorized modifications to the filesystem.

This fulfills requirements for PCI-DSS compliance and **NIST SP 800-53 SI-7 (Software, Firmware, and Information Integrity)**.

## 18.2 Technical Implementation (SHA-256)
The module maintains a list of highly critical OS paths (e.g., `C:\Windows\System32\drivers\etc\hosts`). 
During an audit, the engine reads the file sequentially in 4096-byte blocks to conserve memory, passing the data through the `hashlib.sha256()` cryptographic algorithm.

```python
import hashlib
import sqlite3

def hash_file(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256.update(byte_block)
    return sha256.hexdigest()
```

### Database Persistence
The generated hash is compared against the `fim_baselines` table in the SQLite `audit_history.db`.
If no baseline exists (the first time the scan runs), the engine records the hash as the definitive baseline.

## 18.3 Vulnerability Logic
- **CRITICAL (FIM-001):** If the current SHA-256 hash does not match the baseline hash. This is a massive Indicator of Compromise (IoC). For example, modifying the `hosts` file allows malware to redirect DNS requests for bank websites to attacker-controlled phishing infrastructure.
- **HIGH (FIM-002):** If a critical file is suddenly missing or inaccessible.
