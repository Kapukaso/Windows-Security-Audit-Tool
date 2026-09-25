# Phase 20: CVE Lookup

## 20.1 Academic Overview & Motivation
A large attack surface for Windows endpoints comes from outdated third-party software containing known vulnerabilities. Phase 20 introduces an automated mechanism to cross-reference installed applications against the National Vulnerability Database (NVD) to identify Common Vulnerabilities and Exposures (CVEs).

This maps directly to **CIS Control 7: Continuous Vulnerability Management**.

## 20.2 Technical Implementation (NIST NVD API)
The `modules/cve_lookup.py` module integrates with the public NIST NVD API (`https://services.nvd.nist.gov/rest/json/cves/2.0`). It filters out obvious OS components or generic Microsoft redistributables to save API calls and focuses on third-party software.

To respect NIST's public API limits (without an API key), the module enforces a rate limit (e.g., 6 seconds between requests).

## 20.3 Vulnerability Logic
- **HIGH (CVE-001):** If a known vulnerability is found for an installed application. The engine triggers a HIGH severity finding indicating that the software has documented CVEs and should be updated or uninstalled immediately.
