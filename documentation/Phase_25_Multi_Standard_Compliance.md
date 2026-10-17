# Phase 25: Multi-Standard Compliance Engine

## 25.1 Academic Overview
Regulatory and security compliance frameworks provide standardized benchmarks for evaluating organizational endpoint security posture. Phase 25 introduces a multi-standard compliance engine (`modules/compliance.py`) that cross-references audit findings against four major cybersecurity frameworks:
1. **CIS Benchmarks** (Center for Internet Security)
2. **NIST SP 800-53 Rev. 5** (National Institute of Standards and Technology)
3. **ISO/IEC 27001:2022** (International Organization for Standardization)
4. **HIPAA Security Rule** (45 CFR Part 164, Subpart C)

---

## 25.2 Technical Implementation (`modules/compliance.py`)

Rather than requiring separate manual audits for each standard, `modules/compliance.py` evaluates finding IDs emitted by collectors and dynamically computes compliance scores and rule verification states.

### Supported Frameworks & Control Mappings

| Standard | Control ID | Requirement Description | Mapped Finding IDs |
|----------|------------|-------------------------|---------------------|
| **CIS** | CIS 2.1 | Ensure User Account Control (UAC) is enabled | `REG-004` |
| **CIS** | CIS 2.2 | Ensure NTLMv2 is strictly enforced | `POL-003` |
| **CIS** | CIS 2.3 | Ensure Windows Defender Real-Time Protection is enabled | `DEF-001` |
| **CIS** | CIS 2.4 | Ensure Windows Defender Antivirus signatures are up-to-date | `DEF-002` |
| **CIS** | CIS 2.5 | Ensure Windows Firewall is active for all network profiles | `FW-001`, `FW-002`, `FW-003` |
| **CIS** | CIS 2.6 | Ensure Password Complexity requirements are enabled | `POL-001` |
| **CIS** | CIS 2.7 | Ensure Minimum Password Length is at least 14 characters | `POL-002` |
| **CIS** | CIS 2.8 | Ensure Guest account is disabled | `USR-002` |
| **CIS** | CIS 3.14 | Monitor critical system files for unauthorized modifications (FIM) | `FIM-001` |
| **CIS** | CIS 4.1 | Ensure system has applied recent security patches | `UPD-001` |
| **NIST SP 800-53** | AC-2 | Account Management | `USR-001`, `USR-002` |
| **NIST SP 800-53** | AC-3 | Access Enforcement | `REG-001`, `REG-002` |
| **NIST SP 800-53** | AC-7 | Unsuccessful Logon Attempts | `POL-004` |
| **NIST SP 800-53** | IA-5 | Authenticator Management | `POL-001`, `POL-002` |
| **NIST SP 800-53** | SC-7 | Boundary Protection | `FW-001`, `FW-002`, `FW-003`, `PORT-001` |
| **NIST SP 800-53** | SI-2 | Flaw Remediation | `UPD-001`, `CVE-*` |
| **NIST SP 800-53** | SI-3 | Malicious Code Protection | `DEF-001`, `DEF-002`, `DRV-001` |
| **NIST SP 800-53** | SI-4 | Information System Monitoring | `LOG-001`, `IOC-001`, `IOC-002` |
| **NIST SP 800-53** | SI-7 | Software, Firmware, and Information Integrity | `FIM-001` |
| **ISO/IEC 27001** | A.8.2 | Privileged Access Rights | `USR-001`, `REG-001` |
| **ISO/IEC 27001** | A.8.7 | Protection Against Malware | `DEF-001`, `DEF-002`, `DRV-001` |
| **ISO/IEC 27001** | A.8.8 | Management of Technical Vulnerabilities | `UPD-001`, `CVE-*` |
| **ISO/IEC 27001** | A.8.20 | Network Security | `FW-001`, `FW-002`, `FW-003`, `PORT-001` |
| **ISO/IEC 27001** | A.8.24 | Use of Cryptography | `POL-003`, `REG-002` |
| **HIPAA** | § 164.308(a)(1) | Security Management Process | `UPD-001`, `LOG-001` |
| **HIPAA** | § 164.308(a)(5) | Security Awareness and Training (Malware Protection) | `DEF-001`, `DEF-002` |
| **HIPAA** | § 164.312(a)(1) | Access Control | `USR-001`, `POL-001`, `POL-002` |
| **HIPAA** | § 164.312(b) | Audit Controls | `LOG-001` |
| **HIPAA** | § 164.312(c)(1) | Integrity Controls | `FIM-001` |
| **HIPAA** | § 164.312(e)(1) | Transmission Security | `FW-001`, `PORT-001` |

---

## 25.3 Evaluation Logic & Compliance Scoring

For each framework, `modules/compliance.py` computes:
* **Rule Status**: If any mapped finding is present in `all_findings`, the control status is marked `FAIL` with specific remediation guidance and evidence. Otherwise, it is marked `PASS`.
* **Compliance Score Percentage**:
  $$\text{Score} = \left( \frac{\text{Passed Rules}}{\text{Total Rules}} \right) \times 100$$
* **Report Integration**: Compliance data is returned alongside audit findings in `/api/scan` and embedded into the HTML and JSON report outputs.
