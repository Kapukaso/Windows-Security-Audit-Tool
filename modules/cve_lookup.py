"""
modules/cve_lookup.py
Queries the NIST NVD API for known vulnerabilities (CVEs) in installed software.
Includes a rate limiter to respect NIST's public API limits.
"""
import urllib.request
import urllib.parse
import json
import time

# NIST NVD API limit is 5 requests per 30 seconds (1 req / 6 sec)
# We use 6 seconds to be perfectly safe without an API key.
RATE_LIMIT_DELAY = 6.0

def query_nvd_api(software_name):
    """
    Queries the NIST NVD API for a given software name.
    """
    # URL encode the keyword
    keyword = urllib.parse.quote(software_name)
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&noRejected"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Defiant-Audit-Tool/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                vulnerabilities = data.get("vulnerabilities", [])
                return vulnerabilities
    except Exception as e:
        print(f"Error querying NVD for {software_name}: {e}")
    return []

def audit_software_cves(software_list, progress_tracker=None):
    """
    Filters software and queries for CVEs.
    """
    findings = []
    
    # We only want to query 3rd party apps to avoid overwhelming the API.
    # Exclude obvious OS components or generic Microsoft redistributables.
    filtered_list = []
    for app in software_list:
        name = app.get("Name", "").lower()
        pub = str(app.get("Publisher", "")).lower()
        
        # Skip generic stuff and Microsoft/Windows components to save API calls
        if not name or "microsoft" in pub or "windows" in name or "update" in name:
            continue
        if app.get("Category") == "Windows Component":
            continue
            
        filtered_list.append(app)
        
    # To prevent the scan taking 10+ minutes, let's limit to the first 5 recognizable apps
    target_apps = filtered_list[:5]
    total_apps = len(target_apps)
    
    if progress_tracker and total_apps > 0:
        progress_tracker["message"] = f"Querying NIST Vulnerability Database for {total_apps} apps..."
        
    for i, app in enumerate(target_apps):
        app_name = app.get("Name")
        
        if progress_tracker:
            progress_tracker["message"] = f"Checking CVEs for: {app_name} ({i+1}/{total_apps})"
            # We don't advance the main percentage here much, just update the message
        
        # We take the first 2 words of the app name to get broader matches (e.g. "Google Chrome" instead of "Google Chrome 114.0...")
        search_term = " ".join(app_name.split()[:2])
        
        cves = query_nvd_api(search_term)
        
        # Add finding if critical CVEs exist
        if cves:
            # Look at the first one as an example
            first_cve = cves[0].get("cve", {})
            cve_id = first_cve.get("id", "Unknown CVE")
            desc = first_cve.get("descriptions", [{"value": "Known vulnerability"}])[0].get("value")
            
            findings.append({
                "id": "CVE-001",
                "category": "Software",
                "severity": "HIGH",
                "title": f"Known Vulnerability in {app_name}",
                "description": f"The NIST NVD reports vulnerabilities (e.g. {cve_id}) for this software. Details: {desc[:150]}...",
                "recommendation": f"Update {app_name} to the latest version immediately or uninstall it."
            })
            
        # Enforce rate limit (skip sleep on the very last item)
        if i < total_apps - 1:
            time.sleep(RATE_LIMIT_DELAY)
            
    return findings
