"""
modules/software.py

Collects and analyzes installed software on Windows.
"""

from tabulate import tabulate
from utils.powershell import run_powershell_json


def categorize_software(program):
    """
    Categorize installed software using simple heuristics.
    """

    name = program["Name"].lower()

    # Drivers
    if any(keyword in name for keyword in [
        "driver",
        "nvidia",
        "physx"
    ]):
        return "Driver"

    # Development tools
    if any(keyword in name for keyword in [
        "visual studio",
        "vs code",
        "git",
        "github desktop",
        "node.js",
        "rustup",
        "packet tracer"
    ]):
        return "Development Tool"

    # Runtime / dependencies
    if any(keyword in name for keyword in [
        "visual c++",
        "runtime",
        "python",
        "tcl/tk",
        "standard library",
        "development libraries",
        "redistributable",
        "universal crt"
    ]):
        return "Runtime / Dependency"

    # Windows components
    if any(keyword in name for keyword in [
        "windows sdk",
        "windows app certification",
        "windows team extension",
        "windows mobile extension",
        "application verifier",
        "update health tools"
    ]):
        return "Windows Component"

    return "Application"


def analyze_software_risk(software_list):
    """
    Analyzes the software list for basic security findings.
    """
    findings = []
    
    for program in software_list:
        name = program["Name"].lower()
        publisher = program["Publisher"]
        
        # Check for unknown publishers
        if publisher == "Unknown":
            findings.append({
                "id": "SOFT-001",
                "title": "Software with Unknown Publisher",
                "category": "Software",
                "severity": "LOW",
                "description": f"The software '{program['Name']}' does not have a verified publisher.",
                "recommendation": "Verify if this software is legitimate or remove it if unnecessary."
            })
            
        # Check for potentially risky tools (e.g., torrent clients, hacking tools)
        risky_keywords = ["torrent", "wireshark", "nmap", "keylogger", "cheat engine"]
        if any(keyword in name for keyword in risky_keywords):
            findings.append({
                "id": "SOFT-002",
                "title": "Potentially Risky Software Detected",
                "category": "Software",
                "severity": "MEDIUM",
                "description": f"The software '{program['Name']}' is often used for peer-to-peer sharing or network scanning.",
                "recommendation": "Ensure this tool is authorized on this system."
            })
            
    return findings


def get_installed_software():
    """
    Retrieves installed software from the Windows Registry, deduplicates entries,
    and returns a payload containing the software list, statistics, and findings.
    """

    command = r"""
    $paths = @(
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    $software = foreach ($path in $paths) {

        Get-ItemProperty $path -ErrorAction SilentlyContinue |
        Where-Object { $_.DisplayName } |
        Select-Object DisplayName, DisplayVersion, Publisher, InstallLocation
    }

    $software | ConvertTo-Json -Depth 3
    """

    result = run_powershell_json(command)

    # PowerShell failed
    if isinstance(result, dict) and "error" in result:
        return result

    # If only one item exists, PowerShell returns a dictionary.
    if isinstance(result, dict):
        result = [result]

    cleaned_software = []
    seen = set()

    # Process EVERY installed program
    for program in result:
        name = program.get("DisplayName")

        # Ignore entries without a name
        if not name:
            continue

        version = program.get("DisplayVersion")
        publisher = program.get("Publisher")
        location = program.get("InstallLocation")

        # Normalize missing values
        if not version:
            version = "Unknown"

        if not publisher:
            publisher = "Unknown"

        if not location:
            location = "Unknown"

        name_stripped = name.strip()
        
        # Deduplication using Name and Version as a composite key
        unique_key = f"{name_stripped}::{version}"
        if unique_key in seen:
            continue
        seen.add(unique_key)

        software_item = {
            "Name": name_stripped,
            "Version": version,
            "Publisher": publisher.strip() if isinstance(publisher, str) else publisher,
            "Install Location": location
        }

        # Add category
        software_item["Category"] = categorize_software(software_item)

        # Add item to our final list
        cleaned_software.append(software_item)

    # Compute inventory statistics
    stats = {}
    for item in cleaned_software:
        cat = item["Category"]
        stats[cat] = stats.get(cat, 0) + 1

    # Generate security findings
    findings = analyze_software_risk(cleaned_software)

    return {
        "software": cleaned_software,
        "statistics": stats,
        "findings": findings
    }


def display_software(result, extra_findings=None):
    """
    Display installed software, statistics, and findings.
    Optionally accepts extra_findings (e.g. CVE results) to merge in.
    """

    if isinstance(result, dict) and "error" in result:
        print(f"Error: {result['error']}")
        return

    software = result.get("software", [])
    stats = result.get("statistics", {})
    findings = list(result.get("findings", []))
    if extra_findings:
        findings.extend(extra_findings)

    table = []
    for program in software:
        table.append([
            program["Name"][:50],  # Truncate long names for better CLI output
            program["Version"][:15],
            str(program["Publisher"])[:25],
            program["Category"]
        ])

    print("\n--- Installed Software Inventory ---")
    print(
        tabulate(
            table,
            headers=["Application", "Version", "Publisher", "Category"],
            tablefmt="grid"
        )
    )

    print("\n--- Inventory Statistics ---")
    print(f"Total Unique Applications: {len(software)}")
    for cat, count in stats.items():
        print(f"- {cat}: {count}")

    print("\n--- Security Findings ---")
    if not findings:
        print("No significant software risks detected.")
    else:
        for f in findings:
            print(f"[{f['severity']}] {f['title']}")
            print(f"  > {f['description']}")
            print(f"  > Recommendation: {f['recommendation']}\n")
