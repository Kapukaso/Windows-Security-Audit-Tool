# Phase 9: Password Policy

## 9.1 Academic Overview & Motivation
Identity attacks, specifically credential brute-forcing and password spraying, remain highly effective against endpoints with weak authentication policies. Phase 9 audits the Local Security Policy to ensure the endpoint enforces strong cryptography and account lockout defenses.

## 9.2 Technical Implementation
The module interfaces with the legacy Windows binary `net.exe` via `subprocess`.
It executes `net accounts` and parses the standard output using string manipulation to extract numerical thresholds.

```python
import subprocess
result = subprocess.run(["net", "accounts"], capture_output=True, text=True)
lines = result.stdout.split('\n')
# Example extraction:
# "Minimum password length:            8" -> integer 8
```

## 9.3 Vulnerability Logic & Hardening
- **HIGH (POL-001):** Minimum password length is < 8 characters. (NIST SP 800-63B recommends 8+).
- **HIGH (POL-002):** Account lockout threshold is set to `0` (Never lock out). This permits infinite password guessing.

**Automated Remediation:** This module heavily integrates with Phase 15. The dashboard provides a 1-click remediation action that executes `net accounts /minpwlen:8` and `/lockoutthreshold:5` to instantly harden the endpoint.
