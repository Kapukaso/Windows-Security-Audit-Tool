# Phase 21: Registry Security

## 21.1 Academic Overview & Motivation
The Windows Registry acts as the central hierarchical database used to store information necessary to configure the system. Misconfigurations in critical registry keys can lead to privilege escalation, weakened authentication, or the disabling of core security mechanisms.

This phase audits these specific high-value keys to ensure compliance with security baselines.

## 21.2 Technical Implementation
The `modules/registry.py` module uses PowerShell to query critical registry paths:
- **UAC Settings:** `HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` (`EnableLUA`)
- **NTLMv2 Enforcement:** `HKLM:\SYSTEM\CurrentControlSet\Control\Lsa` (`lmcompatibilitylevel`)
- **Defender Tamper Protection:** `HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender` (`DisableAntiSpyware`)
- **SMB Signing:** `HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters` (`requiresecuritysignature`)

## 21.3 Vulnerability Logic
- **CRITICAL (REG-001):** User Account Control (UAC) is completely disabled (`EnableLUA` = 0).
- **HIGH (REG-002):** Weak LAN Manager Auth Level (`LMCompatibilityLevel` < 5), meaning NTLMv2 is not strictly enforced.
- **CRITICAL (REG-003):** Windows Defender is globally disabled via policy (`DisableAntiSpyware` = 1).
- **MEDIUM (REG-004):** SMB Signing is not enforced (`RequireSecuritySignature` != 1), making the system vulnerable to relay attacks.
