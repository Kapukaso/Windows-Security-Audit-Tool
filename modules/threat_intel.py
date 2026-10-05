"""
modules/threat_intel.py
Threat Intelligence Engine: Correlates local telemetry with IOCs, hashes, and bad command patterns.
"""
import psutil
import hashlib
import os
import urllib.request
import json

# Advanced Threat Intel Patterns mapping to MITRE ATT&CK
THREAT_PATTERNS = {
    "T1059.001": {
        "name": "PowerShell Execution",
        "patterns": ["-nop -w hidden", "-EncodedCommand", "bypass -c", "IEX (New-Object"],
        "severity": "CRITICAL"
    },
    "T1490": {
        "name": "Inhibit System Recovery",
        "patterns": ["vssadmin delete shadows", "bcdedit /set {default} recoveryenabled No", "wbadmin delete catalog"],
        "severity": "CRITICAL"
    },
    "T1105": {
        "name": "Ingress Tool Transfer",
        "patterns": ["certutil.exe -urlcache -split -f", "bitsadmin /transfer"],
        "severity": "HIGH"
    },
    "T1543.003": {
        "name": "Windows Service Execution",
        "patterns": ["sc create", "sc config binPath="],
        "severity": "MEDIUM"
    }
}

# Simulated External Threat Intel Feed (Could be swapped for AlienVault OTX / MISP API)
LOCAL_IOC_DATABASE = {
    "bad_hashes": [
        "44d88612fea8a8f36de82e1278abb02f",  # Wannacry (MD5 example, we should use SHA256 ideally but just examples)
        "5e5f5f4a7c06eb862f92f66ab5cf73a628a8d1df8c2bc804c27dc98deed8b3c9"  # Mock bad hash
    ],
    "bad_ips": [
        "185.11.12.13",
        "45.22.33.44",
        "91.121.23.23" # Typical scanner/C2 mock IPs
    ]
}

def get_file_sha256(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()
    except Exception:
        return None

import os
import json
import urllib.request
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# CrowdStrike Falcon API Credentials
FALCON_CLIENT_ID = os.getenv("FALCON_CLIENT_ID")
FALCON_CLIENT_SECRET = os.getenv("FALCON_CLIENT_SECRET")
FALCON_BASE_URL = os.getenv("FALCON_BASE_URL", "https://api.crowdstrike.com")

def fetch_crowdstrike_iocs():
    """
    Authenticates with CrowdStrike Falcon OAuth2 API and downloads the latest active IOCs.
    """
    if not FALCON_CLIENT_ID or not FALCON_CLIENT_SECRET:
        print("[!] No CrowdStrike credentials found in .env. Falling back to local offline IOC database.")
        return LOCAL_IOC_DATABASE

    try:
        # 1. Obtain OAuth2 Token
        auth_data = urllib.parse.urlencode({
            'client_id': FALCON_CLIENT_ID,
            'client_secret': FALCON_CLIENT_SECRET
        }).encode('utf-8')
        
        req = urllib.request.Request(f"{FALCON_BASE_URL}/oauth2/token", data=auth_data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=5) as response:
            auth_response = json.loads(response.read().decode())
            token = auth_response.get('access_token')

        if not token:
            return LOCAL_IOC_DATABASE

        # 2. Query Falcon Intel API for high-confidence IOCs (Hashes & IPs)
        # Note: This is a structural template for the /intel/combined/indicators/v1 endpoint
        intel_req = urllib.request.Request(f"{FALCON_BASE_URL}/intel/combined/indicators/v1?filter=malicious_confidence:'high'")
        intel_req.add_header('Authorization', f'Bearer {token}')
        intel_req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(intel_req, timeout=10) as response:
            intel_data = json.loads(response.read().decode())
            
        # Parse CrowdStrike resources into our internal format
        crowdstrike_iocs = {"bad_hashes": [], "bad_ips": []}
        for resource in intel_data.get('resources', []):
            ioc_type = resource.get('type')
            ioc_value = resource.get('indicator')
            
            if ioc_type in ['hash_sha256', 'hash_md5']:
                crowdstrike_iocs["bad_hashes"].append(ioc_value.lower())
            elif ioc_type in ['ip_address', 'ipv4']:
                crowdstrike_iocs["bad_ips"].append(ioc_value)
                
        # Merge CrowdStrike IOCs with our local baseline
        crowdstrike_iocs["bad_hashes"].extend(LOCAL_IOC_DATABASE["bad_hashes"])
        crowdstrike_iocs["bad_ips"].extend(LOCAL_IOC_DATABASE["bad_ips"])
        
        return crowdstrike_iocs
        
    except Exception as e:
        print(f"[-] CrowdStrike API Error: {e}. Falling back to local database.")
        return LOCAL_IOC_DATABASE

def download_latest_ioc_feed():
    """
    Fetches the latest IOCs from CrowdStrike Falcon.
    """
    return fetch_crowdstrike_iocs()

def scan_threat_intel():
    """
    Scans running processes, command lines, and active connections against the Threat Intel IOCs.
    """
    findings = []
    iocs = download_latest_ioc_feed()
    
    # Track evaluated EXEs to avoid redundant hashing
    evaluated_hashes = {}

    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'connections']):
            try:
                exe = proc.info.get('exe')
                cmdline = proc.info.get('cmdline')
                conns = proc.info.get('connections')
                
                # 1. Command Line Pattern Matching
                if cmdline:
                    cmd_str = " ".join(cmdline).lower()
                    for mitre_id, rule in THREAT_PATTERNS.items():
                        for pattern in rule["patterns"]:
                            if pattern.lower() in cmd_str:
                                findings.append({
                                    "id": f"THREAT-CMD-{proc.info['pid']}",
                                    "category": "Threat Intel",
                                    "severity": rule["severity"],
                                    "title": f"Suspicious Command Line (MITRE {mitre_id})",
                                    "description": f"Process {proc.info['name']} (PID {proc.info['pid']}) matched known bad pattern '{pattern}'. Tactic: {rule['name']}.",
                                    "recommendation": "Investigate process tree and terminate immediately if unauthorized."
                                })
                                break # Stop checking patterns for this specific rule
                
                # 2. Malicious Process Hashing (IOC Match)
                if exe and exe not in evaluated_hashes:
                    h = get_file_sha256(exe)
                    evaluated_hashes[exe] = h
                    if h in iocs["bad_hashes"]:
                        findings.append({
                            "id": f"THREAT-HASH-{proc.info['pid']}",
                            "category": "Threat Intel",
                            "severity": "CRITICAL",
                            "title": "Malicious Process Hash Detected",
                            "description": f"Process {exe} matches a known bad SHA-256 IOC.",
                            "recommendation": "Isolate host and execute incident response playbook."
                        })
                
                # 3. Active C2 Network Connection (IOC Match)
                if conns:
                    for conn in conns:
                        if conn.status == 'ESTABLISHED' and conn.raddr:
                            remote_ip = conn.raddr.ip
                            if remote_ip in iocs["bad_ips"]:
                                findings.append({
                                    "id": f"THREAT-NET-{proc.info['pid']}",
                                    "category": "Threat Intel",
                                    "severity": "CRITICAL",
                                    "title": f"Command & Control Connection (MITRE T1071)",
                                    "description": f"Process {proc.info['name']} has an established connection to known bad IOC IP: {remote_ip}",
                                    "recommendation": "Block IP at perimeter firewall and terminate process."
                                })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
    except Exception as e:
        findings.append({
            "id": "THREAT-ERR",
            "category": "Threat Intel",
            "severity": "MEDIUM",
            "title": "Threat Intel Engine Failure",
            "description": str(e)
        })

    return findings
