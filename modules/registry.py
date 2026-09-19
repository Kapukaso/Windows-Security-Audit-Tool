"""
modules/registry.py
Audits critical Windows Registry security configurations.
"""
from utils.powershell import run_powershell_json

def get_registry_security():
    command = r"""
    $results = @()
    
    # Check UAC Settings
    $uac = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' -Name 'EnableLUA' -ErrorAction SilentlyContinue
    if ($uac) {
        $results += @{ Name = "UAC_EnableLUA"; Value = $uac.EnableLUA }
    } else {
        $results += @{ Name = "UAC_EnableLUA"; Value = $null }
    }
    
    # Check NTLMv2 Enforcement (LAN Manager Authentication Level)
    $lm = Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name 'lmcompatibilitylevel' -ErrorAction SilentlyContinue
    if ($lm) {
        $results += @{ Name = "LMCompatibilityLevel"; Value = $lm.lmcompatibilitylevel }
    } else {
        $results += @{ Name = "LMCompatibilityLevel"; Value = $null }
    }
    
    # Check Windows Defender Tamper Protection Bypass
    $tamper = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender' -Name 'DisableAntiSpyware' -ErrorAction SilentlyContinue
    if ($tamper) {
        $results += @{ Name = "DisableAntiSpyware"; Value = $tamper.DisableAntiSpyware }
    } else {
        $results += @{ Name = "DisableAntiSpyware"; Value = $null }
    }
    
    # Check SMB Signing
    $smb = Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters' -Name 'requiresecuritysignature' -ErrorAction SilentlyContinue
    if ($smb) {
        $results += @{ Name = "RequireSecuritySignature"; Value = $smb.requiresecuritysignature }
    } else {
        $results += @{ Name = "RequireSecuritySignature"; Value = $null }
    }

    $results | ConvertTo-Json
    """
    result = run_powershell_json(command)
    return result

def assess_registry(registry_data):
    findings = []
    
    if isinstance(registry_data, dict) and "error" in registry_data:
        return findings
        
    for item in registry_data:
        name = item.get("Name")
        value = item.get("Value")
        
        if name == "UAC_EnableLUA" and value == 0:
            findings.append({
                "id": "REG-001",
                "category": "Registry",
                "severity": "CRITICAL",
                "title": "User Account Control (UAC) Disabled",
                "description": "UAC is completely disabled in the registry.",
                "recommendation": "Enable UAC to prevent unauthorized execution of privileged processes."
            })
            
        elif name == "LMCompatibilityLevel":
            if value is None or value < 5:
                findings.append({
                    "id": "REG-002",
                    "category": "Registry",
                    "severity": "HIGH",
                    "title": "Weak LAN Manager Auth Level",
                    "description": f"LMCompatibilityLevel is set to {value}. NTLMv2 is not strictly enforced.",
                    "recommendation": "Set LMCompatibilityLevel to 5 to send NTLMv2 responses only and refuse LM & NTLM."
                })
                
        elif name == "DisableAntiSpyware" and value == 1:
            findings.append({
                "id": "REG-003",
                "category": "Registry",
                "severity": "CRITICAL",
                "title": "Defender Disabled via Policy",
                "description": "Windows Defender has been globally disabled in the registry.",
                "recommendation": "Remove the DisableAntiSpyware key or set it to 0."
            })
            
        elif name == "RequireSecuritySignature" and value != 1:
            findings.append({
                "id": "REG-004",
                "category": "Registry",
                "severity": "MEDIUM",
                "title": "SMB Signing Not Enforced",
                "description": "SMB communication may be vulnerable to relay attacks.",
                "recommendation": "Set RequireSecuritySignature to 1."
            })

    return findings

def display_registry(registry_data, findings):
    print("\n--- Registry Security Findings ---")
    if not findings:
        print("No registry vulnerabilities detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
