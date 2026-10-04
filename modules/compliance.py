"""
modules/compliance.py
Cross-references findings against major regulatory frameworks.
"""
from tabulate import tabulate

COMPLIANCE_MAPPINGS = [
    {
        "finding_id": "REG-001",
        "frameworks": {
            "CIS": "CIS 2.1 (UAC Settings)",
            "NIST": "NIST AC-6 (Least Privilege)",
            "STIG": "V-220739 (UAC Enabled)",
            "ISO 27001": "A.9.2.3 (Privileged Rights)",
            "HIPAA": "164.312(a)(1) (Access Control)",
            "PCI": "Req 7.1.2 (Restrict Privileged IDs)"
        },
        "description": "Ensure User Account Control (UAC) is enabled."
    },
    {
        "finding_id": "REG-002",
        "frameworks": {
            "CIS": "CIS 2.2 (NTLMv2)",
            "NIST": "NIST IA-5 (Authenticator Management)",
            "STIG": "V-220743 (LM Compatibility Level)",
            "ISO 27001": "A.9.4.3 (Password Management)",
            "HIPAA": "164.312(d) (Authentication)",
            "PCI": "Req 8.2.1 (Strong Cryptography)"
        },
        "description": "Ensure NTLMv2 is strictly enforced."
    },
    {
        "finding_id": "FIM-001",
        "frameworks": {
            "CIS": "CIS 3.14 (File Integrity Monitoring)",
            "NIST": "NIST SI-7 (Information Integrity)",
            "STIG": "V-220745 (File Integrity)",
            "ISO 27001": "A.12.2.1 (Malware Controls)",
            "HIPAA": "164.312(c)(1) (Integrity)",
            "PCI": "Req 11.5 (Deploy FIM Tools)"
        },
        "description": "Monitor critical system files for unauthorized modifications."
    },
    {
        "finding_id": "UPD-003",
        "frameworks": {
            "CIS": "CIS 7.1 (Vulnerability Management)",
            "NIST": "NIST SI-2 (Flaw Remediation)",
            "STIG": "V-220746 (System Updates)",
            "ISO 27001": "A.12.6.1 (Technical Vulnerabilities)",
            "HIPAA": "164.308(a)(5)(ii)(B) (Patch Management)",
            "PCI": "Req 6.2 (Protect from Known Vulnerabilities)"
        },
        "description": "Ensure the system has applied recent security patches."
    },
    {
        "finding_id": "EVT-001",
        "frameworks": {
            "CIS": "CIS 8.2 (Collect Audit Logs)",
            "NIST": "NIST AU-2 (Event Logging)",
            "STIG": "V-220748 (Audit Event Logging)",
            "ISO 27001": "A.12.4.1 (Event Logging)",
            "HIPAA": "164.312(b) (Audit Controls)",
            "PCI": "Req 10.1 (Implement Audit Trails)"
        },
        "description": "Ensure Security Event Logs are being generated and collected."
    },
    {
        "finding_id": "DEF-001",
        "frameworks": {
            "CIS": "CIS 10.1 (Anti-Malware)",
            "NIST": "NIST SI-3 (Malicious Code Protection)",
            "STIG": "V-220749 (Endpoint Security)",
            "ISO 27001": "A.12.2.1 (Malware Controls)",
            "HIPAA": "164.308(a)(5)(ii)(B) (Malware Protection)",
            "PCI": "Req 5.1 (Deploy Anti-Virus Software)"
        },
        "description": "Ensure Windows Defender Real-Time Protection is active."
    },
    {
        "finding_id": "FW-001",
        "frameworks": {
            "CIS": "CIS 9.1 (Host-Based Firewalls)",
            "NIST": "NIST SC-7 (Boundary Protection)",
            "STIG": "V-220750 (Windows Firewall)",
            "ISO 27001": "A.13.1.1 (Network Controls)",
            "HIPAA": "164.312(e)(1) (Transmission Security)",
            "PCI": "Req 1.1 (Establish Firewall Configuration)"
        },
        "description": "Ensure Windows Firewall is enabled for all profiles."
    },
    {
        "finding_id": "POL-001",
        "frameworks": {
            "CIS": "CIS 4.1 (Password Policy)",
            "NIST": "NIST IA-5 (Authenticator Management)",
            "STIG": "V-220751 (Password Length)",
            "ISO 27001": "A.9.4.3 (Password Management)",
            "HIPAA": "164.308(a)(5)(ii)(D) (Password Management)",
            "PCI": "Req 8.2.3 (Minimum Password Length)"
        },
        "description": "Ensure minimum password length is at least 14 characters."
    },
    {
        "finding_id": "NET-003",
        "frameworks": {
            "CIS": "CIS 9.2 (Restrict Insecure Protocols)",
            "NIST": "NIST SC-8 (Transmission Confidentiality)",
            "STIG": "V-220752 (Legacy Protocols)",
            "ISO 27001": "A.13.2.1 (Information Transfer)",
            "HIPAA": "164.312(e)(1) (Transmission Security)",
            "PCI": "Req 2.2.3 (Implement Secure Protocols)"
        },
        "description": "Ensure insecure legacy protocols (like Telnet/FTP) are not listening."
    },
    {
        "finding_id": "USR-001", 
        "frameworks": {
            "CIS": "CIS 5.1 (Establish Secure Configurations)",
            "NIST": "NIST AC-2 (Account Management)",
            "STIG": "V-220753 (Administrator Accounts)",
            "ISO 27001": "A.9.2.1 (User Registration)",
            "HIPAA": "164.308(a)(4)(ii)(B) (Access Authorization)",
            "PCI": "Req 7.1.1 (Define Access Needs)"
        },
        "description": "Ensure unauthorized accounts are not in the Local Administrators group."
    }
]

def generate_compliance_report(all_findings):
    """
    Evaluates current findings against known compliance frameworks.
    Returns a dictionary of frameworks containing passing/failing rules.
    """
    # Create a dict mapping finding IDs to their finding objects for quick lookup
    active_findings = {f.get("id"): f for f in all_findings if isinstance(f, dict) and "id" in f}
    
    frameworks = ["CIS", "NIST", "STIG", "ISO 27001", "HIPAA", "PCI"]
    report = {fw: {"passed": 0, "failed": 0, "rules": []} for fw in frameworks}
    
    for rule in COMPLIANCE_MAPPINGS:
        finding_id = rule["finding_id"]
        is_failed = finding_id in active_findings
        
        finding_details = active_findings.get(finding_id)
        
        for fw in frameworks:
            if fw in rule["frameworks"]:
                status = "FAIL" if is_failed else "PASS"
                
                if status == "PASS":
                    report[fw]["passed"] += 1
                else:
                    report[fw]["failed"] += 1
                    
                rule_report = {
                    "requirement": rule["frameworks"][fw],
                    "description": rule["description"],
                    "status": status,
                    "evidence": finding_details.get("description") if is_failed else "System meets secure baseline configuration.",
                    "fix_guidance": finding_details.get("recommendation") if is_failed else "Maintain current configuration."
                }
                
                report[fw]["rules"].append(rule_report)
                
    for fw in frameworks:
        total = report[fw]["passed"] + report[fw]["failed"]
        if total > 0:
            report[fw]["compliance_score"] = round((report[fw]["passed"] / total) * 100, 1)
        else:
            report[fw]["compliance_score"] = 100.0
            
    return report

def display_compliance_report(report):
    print("\n" + "=" * 60)
    print("COMPLIANCE BASELINE ASSESSMENT")
    print("=" * 60)
    
    summary_table = []
    for fw, data in report.items():
        summary_table.append([fw, f"{data['passed']}", f"{data['failed']}", f"{data['compliance_score']}%"])
        
    print(
        tabulate(
            summary_table,
            headers=["Framework", "Passed", "Failed", "Compliance Score"],
            tablefmt="grid"
        )
    )
    
    print("\n[!] Note: Detailed evidence and fix guidance is available in the JSON report.")
