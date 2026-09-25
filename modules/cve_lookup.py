"""
modules/cve_lookup.py
Queries the NIST NVD API for known vulnerabilities (CVEs) in installed software.
Supports the use of an NVD API key to increase rate limits.
"""
import urllib.request
import urllib.parse
import json
import time
import os
import sys

# Default to None
NVD_API_KEY = None

# Attempt to load from a persistent config file in the user's home directory
try:
    home_dir = os.path.expanduser("~")
    config_path = os.path.join(home_dir, '.defiant_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            NVD_API_KEY = config_data.get("NVD_API_KEY")
except Exception:
    pass

# NIST NVD limits: 
# Without API Key: 5 requests per 30 seconds (1 req / 6 sec)
# With API Key: 50 requests per 30 seconds (1 req / 0.6 sec)
RATE_LIMIT_DELAY = 0.6 if NVD_API_KEY else 6.0

def query_nvd_api(software_name):
    """
    Queries the NIST NVD API for a given software name.
    """
    keyword = urllib.parse.quote(software_name)
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&noRejected"
    
    headers = {'User-Agent': 'Defiant-Audit-Tool/1.0'}
    if NVD_API_KEY:
        headers['apiKey'] = NVD_API_KEY
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("vulnerabilities", [])
    except Exception as e:
        print(f"Error querying NVD for {software_name}: {e}")
    return []

def audit_software_cves(software_list, progress_tracker=None):
    """
    Filters software and queries for CVEs.
    """
    findings = []
    
    filtered_list = []
    for app in software_list:
        name = app.get("Name", "").lower()
        pub = str(app.get("Publisher", "")).lower()
        
        # Skip generic Microsoft/Windows components to avoid false positives and save API calls
        if not name or "microsoft" in pub or "windows" in name or "update" in name:
            continue
        if app.get("Category") == "Windows Component":
            continue
            
        filtered_list.append(app)
        
    # If no API key is provided, limit to 5 apps to prevent a 10+ minute scan
    target_apps = filtered_list if NVD_API_KEY else filtered_list[:5]
    total_apps = len(target_apps)
    
    if progress_tracker and total_apps > 0:
        progress_tracker["message"] = f"Querying NIST Vulnerability Database for {total_apps} apps..."
        
    for i, app in enumerate(target_apps):
        app_name = app.get("Name")
        
        if progress_tracker:
            progress_tracker["message"] = f"Checking CVEs for: {app_name} ({i+1}/{total_apps})"
        
        search_term = " ".join(app_name.split()[:2])
        cves = query_nvd_api(search_term)
        
        if cves:
            first_cve = cves[0].get("cve", {})
            cve_id = first_cve.get("id", "Unknown CVE")
            desc = first_cve.get("descriptions", [{"value": "Known vulnerability"}])[0].get("value")
            
            findings.append({
                "id": f"CVE|{app_name}",
                "category": "Software",
                "severity": "HIGH",
                "title": f"Known Vulnerability in {app_name}",
                "description": f"The NIST NVD reports vulnerabilities (e.g. {cve_id}) for this software. Details: {desc[:150]}...",
                "recommendation": f"Update {app_name} to the latest version immediately or uninstall it."
            })
            
        if i < total_apps - 1:
            time.sleep(RATE_LIMIT_DELAY)
            
    return findings
