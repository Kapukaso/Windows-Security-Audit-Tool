"""
modules/cve_lookup.py
Queries the NIST NVD API for known vulnerabilities (CVEs) in installed software.
Supports the use of an NVD API key to increase rate limits, local database caching,
and a session circuit breaker to prevent audit freezes.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import os
import sys

from dotenv import load_dotenv
from database.database import get_cve_cache, save_cve_cache

# Ensure environment variables are loaded from .env
load_dotenv()

# NIST NVD API Key from centralized .env
NVD_API_KEY = os.getenv("NVD_API_KEY")

# NIST NVD limits: 
# Without API Key: 5 requests per 30 seconds (1 req / 6 sec)
# With API Key: 50 requests per 30 seconds (1 req / 0.6 sec)
RATE_LIMIT_DELAY = 0.6 if NVD_API_KEY else 6.0

class NVDCircuitBreaker:
    """Session circuit breaker to avoid audit hangs on NVD API rate limits or outages."""
    def __init__(self):
        self.is_open = False
        self.reason = None
        self.consecutive_timeouts = 0

    def record_success(self):
        self.consecutive_timeouts = 0

    def record_failure(self, error_code_or_msg):
        if error_code_or_msg in (429, 403):
            self.is_open = True
            self.reason = f"Rate limited or forbidden (HTTP {error_code_or_msg})"
        elif "timeout" in str(error_code_or_msg).lower():
            self.consecutive_timeouts += 1
            if self.consecutive_timeouts >= 2:
                self.is_open = True
                self.reason = "Consecutive request timeouts"
        elif error_code_or_msg in (500, 502, 503, 504):
            self.is_open = True
            self.reason = f"NVD server error (HTTP {error_code_or_msg})"

def query_nvd_api(software_name, timeout=5):
    """
    Queries the NIST NVD API for a given software name with a strict timeout.
    Returns tuple: (vulnerabilities_list, status_code_or_error)
    """
    keyword = urllib.parse.quote(software_name)
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={keyword}&noRejected"
    
    headers = {'User-Agent': 'Defiant-Audit-Tool/1.0'}
    if NVD_API_KEY:
        headers['apiKey'] = NVD_API_KEY
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return data.get("vulnerabilities", []), 200
    except urllib.error.HTTPError as e:
        return None, e.code
    except urllib.error.URLError as e:
        reason_str = str(e.reason).lower() if hasattr(e, 'reason') else str(e).lower()
        return None, "TIMEOUT" if "timed out" in reason_str else "URL_ERROR"
    except Exception as e:
        return None, "ERROR"
    return [], 200

def _format_cve_finding(app_name, cves):
    """Formats the first CVE from a vulnerabilities list into a standard finding dict."""
    if not cves or not isinstance(cves, list):
        return None
    first_cve = cves[0].get("cve", {})
    cve_id = str(first_cve.get("id", "Unknown CVE")).replace("\x00", "")
    desc_raw = first_cve.get("descriptions", [{"value": "Known vulnerability"}])[0].get("value", "")
    desc = str(desc_raw).replace("\x00", "")
    clean_app_name = str(app_name).replace("\x00", "")
    
    return {
        "id": f"CVE|{clean_app_name}",
        "category": "Software",
        "severity": "HIGH",
        "title": f"Known Vulnerability in {clean_app_name}",
        "description": f"The NIST NVD reports vulnerabilities (e.g. {cve_id}) for this software. Details: {desc[:150]}...",
        "recommendation": f"Update {clean_app_name} to the latest version immediately or uninstall it."
    }

def audit_software_cves(software_list, progress_tracker=None, force_refresh=False):
    """
    Filters software and queries for CVEs using a cache-first approach with circuit breaker protection.
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
        
    # If no API key is provided, limit to 5 apps to prevent long scans on cache misses
    target_apps = filtered_list if NVD_API_KEY else filtered_list[:5]
    total_apps = len(target_apps)
    
    if progress_tracker and total_apps > 0:
        progress_tracker["message"] = f"Querying NIST Vulnerability Database for {total_apps} apps..."
        
    circuit_breaker = NVDCircuitBreaker()
    circuit_breaker_tripped = False

    for i, app in enumerate(target_apps):
        app_name = app.get("Name")
        app_version = app.get("Version")
        version_key = None if not app_version or app_version == "Unknown" else app_version
        
        if progress_tracker:
            progress_tracker["message"] = f"Checking CVEs for: {app_name} ({i+1}/{total_apps})"
        
        # 1. Check local persistent database cache first (7-day TTL)
        if not force_refresh:
            cached_cves = get_cve_cache(app_name, version_key, max_age_days=7)
            if cached_cves is not None:
                finding = _format_cve_finding(app_name, cached_cves)
                if finding:
                    findings.append(finding)
                # Cache hit: instant resolution, zero network sleep delay
                continue
                
        # 2. Cache miss: check session circuit breaker before attempting network call
        if circuit_breaker.is_open:
            continue
            
        # 3. Query external NIST NVD API with strict 5-second timeout
        search_term = " ".join(app_name.split()[:2])
        cves, status = query_nvd_api(search_term, timeout=5)
        
        if status == 200:
            circuit_breaker.record_success()
            # Cache results (including empty list for negative caching)
            save_cve_cache(app_name, version_key, cves)
            
            finding = _format_cve_finding(app_name, cves)
            if finding:
                findings.append(finding)
                
            if i < total_apps - 1:
                time.sleep(RATE_LIMIT_DELAY)
        else:
            circuit_breaker.record_failure(status)
            if circuit_breaker.is_open:
                circuit_breaker_tripped = True
                if progress_tracker:
                    progress_tracker["message"] = f"NVD API unavailable ({circuit_breaker.reason}). Using local cache."

    # 4. If NVD API became unavailable during audit, record a single consolidated informational finding
    if circuit_breaker_tripped or circuit_breaker.is_open:
        findings.append({
            "id": "CVE-NVD-UNAVAILABLE",
            "category": "Software",
            "severity": "INFO",
            "title": "NVD Vulnerability Feed Offline or Rate-Limited",
            "description": f"External queries to the NIST National Vulnerability Database were paused ({circuit_breaker.reason or 'service unreachable'}). Vulnerability inspection completed using local database cache.",
            "recommendation": "Configure a valid NVD_API_KEY in .env to increase rate limits, or retry the scan when network connectivity is restored."
        })
        
    return findings
