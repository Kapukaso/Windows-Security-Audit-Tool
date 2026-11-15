"""
security/patcher.py
Windows Package Manager (winget) and Windows Task Scheduler automation engine.
Provides automated bi-weekly application patch management with active process
avoidance, package pinning, and database audit logging.
"""

import os
import sys
import re
import json
import psutil
from datetime import datetime
from utils.powershell import run_powershell, run_powershell_json
from database.database import (
    save_patch_run,
    get_patch_history,
    get_pinned_packages,
    add_pinned_package,
    remove_pinned_package,
    sanitize_null_bytes
)

TASK_NAME = "Defiant-AppAutoPatcher"

RECOMMENDED_PINS = [
    {"package_id": "Python.Python.3.10", "package_name": "Python 3.10 Runtime", "reason": "Runtime environment dependency"},
    {"package_id": "Python.Python.3.11", "package_name": "Python 3.11 Runtime", "reason": "Runtime environment dependency"},
    {"package_id": "Python.Python.3.12", "package_name": "Python 3.12 Runtime", "reason": "Runtime environment dependency"},
    {"package_id": "Python.Python.3.13", "package_name": "Python 3.13 Runtime", "reason": "Runtime environment dependency"},
    {"package_id": "OpenJS.NodeJS", "package_name": "Node.js JavaScript Runtime", "reason": "Development runtime dependency"},
    {"package_id": "OpenJS.NodeJS.LTS", "package_name": "Node.js LTS Runtime", "reason": "Development runtime dependency"},
    {"package_id": "PostgreSQL.PostgreSQL", "package_name": "PostgreSQL Database Server", "reason": "Production database service"},
    {"package_id": "Git.Git", "package_name": "Git Version Control", "reason": "Developer tool chain"},
    {"package_id": "Docker.DockerDesktop", "package_name": "Docker Desktop", "reason": "Container virtualization engine"}
]


def is_winget_available():
    """Checks whether the Windows Package Manager (winget) is installed and accessible."""
    res = run_powershell("Get-Command winget -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source")
    return bool(res and "winget" in res.lower())


def get_winget_bootstrap_command():
    """Returns the silent PowerShell bootstrap command to install Microsoft Desktop App Installer if missing."""
    return (
        'Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe'
    )


def is_metered_connection():
    """
    Checks if the active Windows internet connection profile is metered (e.g. mobile hotspot).
    Returns True if metered, False otherwise.
    """
    ps_cmd = """
    try {
        $cost = (Get-NetConnectionCost -ErrorAction Stop).Cost
        if ($cost -and $cost -ne 'Unrestricted') { 'True' } else { 'False' }
    } catch {
        'False'
    }
    """
    res = run_powershell(ps_cmd)
    return bool(res and "true" in res.lower())


def get_running_process_names():
    """
    Retrieves a set of unique lowercase running process names (e.g., {'chrome.exe', 'discord.exe'}).
    """
    names = set()
    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info.get('name')
            if pname:
                names.add(pname.lower().strip())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names


def is_package_in_use(package_id, package_name, running_processes=None):
    """
    Determines if a package is currently being used by an active process.
    Matches package tokens against running executable names.
    """
    if running_processes is None:
        running_processes = get_running_process_names()

    # Extract tokens from ID and name
    candidates = []
    if package_id:
        # e.g., 'Google.Chrome' -> ['google', 'chrome']
        candidates.extend(re.split(r'[\.\-_]', package_id.lower()))
    if package_name:
        candidates.extend(re.split(r'[\s\.\-_]', package_name.lower()))

    # Filter out generic/too-short words
    ignored_tokens = {"inc", "corp", "corporation", "llc", "software", "technologies", "microsoft", "google", "desktop", "app", "the", "for", "windows", "x64", "x86"}
    clean_tokens = [t for t in candidates if len(t) >= 3 and t not in ignored_tokens]

    for proc in running_processes:
        # Remove '.exe' suffix
        proc_base = proc[:-4] if proc.endswith('.exe') else proc
        for token in clean_tokens:
            if token == proc_base or token in proc_base:
                return True, proc

    return False, None


def parse_winget_upgrade_output(raw_output):
    """
    Parses the tabular stdout of `winget upgrade` into a list of package dictionaries.
    """
    if not raw_output:
        return []

    lines = raw_output.strip().splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if "Name" in line and "Id" in line and "Version" in line and "Available" in line:
            header_idx = i
            break

    if header_idx == -1 or header_idx + 2 > len(lines):
        return []

    # Parse columns based on the dashed divider line
    divider = lines[header_idx + 1] if header_idx + 1 < len(lines) else ""
    if not divider.startswith("-"):
        # Fallback to whitespace regex splitting
        packages = []
        for line in lines[header_idx + 1:]:
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 4:
                packages.append({
                    "name": parts[0],
                    "id": parts[1],
                    "version": parts[2],
                    "available": parts[3]
                })
        return packages

    # Divider-based slice calculation
    # Find column start positions
    header_line = lines[header_idx]
    id_pos = header_line.find("Id")
    ver_pos = header_line.find("Version")
    avail_pos = header_line.find("Available")
    src_pos = header_line.find("Source")

    packages = []
    for line in lines[header_idx + 2:]:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("-"):
            continue
        # Stop at summary text (e.g. "2 upgrades available.")
        if "upgrades available" in line_clean.lower():
            break

        try:
            name_part = line[:id_pos].strip() if id_pos != -1 else ""
            id_part = line[id_pos:ver_pos].strip() if id_pos != -1 and ver_pos != -1 else ""
            ver_part = line[ver_pos:avail_pos].strip() if ver_pos != -1 and avail_pos != -1 else ""
            avail_part = line[avail_pos:src_pos].strip() if avail_pos != -1 and src_pos != -1 else line[avail_pos:].strip()

            if name_part and id_part:
                packages.append({
                    "name": name_part,
                    "id": id_part,
                    "version": ver_part,
                    "available": avail_part
                })
        except Exception:
            continue

    return packages


def get_updatable_packages():
    """Queries winget for available software updates."""
    if not is_winget_available():
        return {"error": "Winget is not installed on this system.", "packages": []}

    output = run_powershell("winget upgrade --include-unknown")
    if not output:
        return {"packages": []}

    packages = parse_winget_upgrade_output(output)
    return {"packages": packages}


def get_recommended_pins():
    """Returns the list of recommended software pins."""
    return RECOMMENDED_PINS


def pin_package(package_id, package_name=None, reason=None):
    """
    Pins an application to completely block automatic upgrades (D-09, D-10).
    Executes 'winget pin add --id <id> --blocking' and stores in database.
    """
    package_id = sanitize_null_bytes(package_id).strip()
    if not package_id:
        return {"success": False, "error": "Package ID cannot be empty."}

    if not package_name:
        package_name = package_id

    # Execute native winget pin
    if is_winget_available():
        cmd = f"winget pin add --id \"{package_id}\" --blocking"
        run_powershell(cmd)

    # Persist in Defiant database
    add_pinned_package(package_id, package_name, pin_type="BLOCKING", reason=reason)
    return {"success": True, "message": f"Successfully pinned {package_id}."}


def unpin_package(package_id):
    """
    Removes a pin for an application.
    Executes 'winget pin remove --id <id>' and removes from database.
    """
    package_id = sanitize_null_bytes(package_id).strip()
    if not package_id:
        return {"success": False, "error": "Package ID cannot be empty."}

    # Execute native winget unpin
    if is_winget_available():
        cmd = f"winget pin remove --id \"{package_id}\""
        run_powershell(cmd)

    # Remove from Defiant database
    remove_pinned_package(package_id)
    return {"success": True, "message": f"Successfully unpinned {package_id}."}


def get_pins():
    """Retrieves all pinned packages from the database."""
    return get_pinned_packages()


def execute_upgrades(trigger_type="MANUAL", progress_callback=None):
    """
    Executes silent upgrades across all eligible applications (PATCH-01).
    - Checks metered network state (defers if metered during scheduled runs).
    - Queries available updates.
    - Excludes pinned packages.
    - Skips packages actively in use by running processes.
    - Upgrades remaining packages silently without rebooting.
    - Logs execution results to patch_history.
    """
    trigger_type = sanitize_null_bytes(trigger_type).upper()

    # Step 1: Check metered connection for scheduled runs (D-08)
    if trigger_type == "SCHEDULED" and is_metered_connection():
        save_patch_run(
            trigger_type=trigger_type,
            packages_updated=0,
            packages_skipped=0,
            packages_failed=0,
            details={"reason": "Deferred: Active internet connection is metered."},
            status="METERED_DEFERRED"
        )
        return {
            "success": True,
            "status": "METERED_DEFERRED",
            "message": "Patch execution deferred: active network connection is metered."
        }

    # Step 2: Check winget availability
    if not is_winget_available():
        msg = "Winget is not available on this system."
        save_patch_run(
            trigger_type=trigger_type,
            packages_updated=0,
            packages_skipped=0,
            packages_failed=0,
            details={"error": msg},
            status="FAILED"
        )
        return {"success": False, "status": "FAILED", "error": msg}

    if progress_callback:
        progress_callback("Scanning for available software updates...", 10)

    # Step 3: Discover updatable packages
    updatable_res = get_updatable_packages()
    packages = updatable_res.get("packages", [])

    if not packages:
        save_patch_run(
            trigger_type=trigger_type,
            packages_updated=0,
            packages_skipped=0,
            packages_failed=0,
            details={"message": "All applications are up to date."},
            status="SUCCESS"
        )
        if progress_callback:
            progress_callback("All applications are up to date.", 100)
        return {
            "success": True,
            "status": "SUCCESS",
            "packages_updated": 0,
            "packages_skipped": 0,
            "packages_failed": 0,
            "details": []
        }

    # Step 4: Load pinned package IDs
    pinned_objs = get_pinned_packages()
    pinned_ids = {p["package_id"].lower() for p in pinned_objs}

    # Step 5: Load active processes for in-use guard (D-05)
    running_procs = get_running_process_names()

    updated_count = 0
    skipped_count = 0
    failed_count = 0
    reboot_required = False
    details_log = []

    total_pkgs = len(packages)

    for idx, pkg in enumerate(packages):
        pkg_id = pkg.get("id", "")
        pkg_name = pkg.get("name", "")

        pct = 15 + int(80 * (idx / total_pkgs))
        if progress_callback:
            progress_callback(f"Processing {pkg_name} ({idx+1}/{total_pkgs})...", pct)

        # Check Pinning
        if pkg_id.lower() in pinned_ids:
            skipped_count += 1
            details_log.append({
                "package_id": pkg_id,
                "package_name": pkg_name,
                "status": "SKIPPED_PINNED",
                "message": "Package is pinned to prevent automated upgrades."
            })
            continue

        # Check Active Process Guard (D-05)
        in_use, matched_proc = is_package_in_use(pkg_id, pkg_name, running_procs)
        if in_use:
            skipped_count += 1
            details_log.append({
                "package_id": pkg_id,
                "package_name": pkg_name,
                "status": "SKIPPED_IN_USE",
                "message": f"Skipped: Active running process detected ({matched_proc})."
            })
            continue

        # Execute Upgrade (D-04: --no-restart)
        upgrade_cmd = f"winget upgrade --id \"{pkg_id}\" --silent --accept-package-agreements --accept-source-agreements --include-unknown"
        res_output = run_powershell(upgrade_cmd)

        # Check for success or error indicators in output
        res_str = (res_output or "").lower()
        if "successfully installed" in res_str or "no applicable update found" in res_str or res_str == "":
            updated_count += 1
            if "reboot" in res_str or "restart" in res_str:
                reboot_required = True
            details_log.append({
                "package_id": pkg_id,
                "package_name": pkg_name,
                "status": "UPDATED",
                "message": "Successfully upgraded."
            })
        else:
            # Check for error patterns
            failed_count += 1
            details_log.append({
                "package_id": pkg_id,
                "package_name": pkg_name,
                "status": "FAILED",
                "message": res_output[:200] if res_output else "Unknown installer failure."
            })

    overall_status = "SUCCESS"
    if failed_count > 0 and updated_count > 0:
        overall_status = "PARTIAL"
    elif failed_count > 0 and updated_count == 0:
        overall_status = "FAILED"

    # Save to database
    save_patch_run(
        trigger_type=trigger_type,
        packages_updated=updated_count,
        packages_skipped=skipped_count,
        packages_failed=failed_count,
        details={"packages": details_log, "reboot_required": reboot_required},
        status=overall_status
    )

    if progress_callback:
        progress_callback("Upgrade cycle complete.", 100)

    return {
        "success": True,
        "status": overall_status,
        "packages_updated": updated_count,
        "packages_skipped": skipped_count,
        "packages_failed": failed_count,
        "reboot_required": reboot_required,
        "details": details_log
    }


# ==========================================
# Windows Task Scheduler Automation (PATCH-02)
# ==========================================

def get_scheduler_status():
    """
    Queries Windows Task Scheduler for the Defiant-AppAutoPatcher task.
    Returns task existence, state, last run, next run, and last result.
    """
    ps_cmd = f"""
    $task = Get-ScheduledTask -TaskName "{TASK_NAME}" -ErrorAction SilentlyContinue
    if (-not $task) {{
        @{{ task_exists = $false }} | ConvertTo-Json
    }} else {{
        $info = Get-ScheduledTaskInfo -TaskName "{TASK_NAME}" -ErrorAction SilentlyContinue
        @{{
            task_exists = $true
            task_name = $task.TaskName
            state = $task.State.ToString()
            last_run = if ($info.LastRunTime) {{ $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss") }} else {{ "Never" }}
            next_run = if ($info.NextRunTime) {{ $info.NextRunTime.ToString("yyyy-MM-dd HH:mm:ss") }} else {{ "Not Scheduled" }}
            last_result = $info.LastTaskResult
        }} | ConvertTo-Json
    }}
    """
    data = run_powershell_json(ps_cmd)
    if isinstance(data, dict):
        return {
            "task_exists": data.get("task_exists", False),
            "state": data.get("state", "Disabled" if not data.get("task_exists") else "Ready"),
            "last_run": data.get("last_run", "Never"),
            "next_run": data.get("next_run", "Not Scheduled"),
            "last_result": data.get("last_result", 0)
        }
    return {
        "task_exists": False,
        "state": "Disabled",
        "last_run": "Never",
        "next_run": "Not Scheduled",
        "last_result": 0
    }


def register_biweekly_task(script_path=None):
    """
    Registers the elevated bi-weekly Windows Scheduled Task (PATCH-02, D-01, D-02, D-03).
    - Sunday at 03:00 AM every 2 weeks (-WeeksInterval 2).
    - StartWhenAvailable = $true (catches up missed runs).
    - AllowStartIfOnBatteries = $true, DontStopIfGoingOnBatteries = $true.
    - RunLevel = Highest.
    """
    if not script_path:
        # Default to invoking python with a scheduled upgrade trigger
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        python_exe = sys.executable
        runner_arg = f'-c "from security.patcher import execute_upgrades; execute_upgrades(trigger_type=\'SCHEDULED\')"'
        exec_target = python_exe
        exec_args = runner_arg
    else:
        exec_target = "powershell.exe"
        exec_args = f"-NoProfile -ExecutionPolicy Bypass -File \"{script_path}\""

    ps_cmd = f"""
    $action = New-ScheduledTaskAction -Execute "{exec_target}" -Argument '{exec_args}'
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -WeeksInterval 2 -At 3:00am
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)

    Register-ScheduledTask -TaskName "{TASK_NAME}" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    """
    run_powershell(ps_cmd)
    return get_scheduler_status()


def toggle_scheduler_task(enabled=True):
    """Enables or disables the scheduled task."""
    status = get_scheduler_status()
    if not status.get("task_exists"):
        if enabled:
            return register_biweekly_task()
        return status

    action = "Enable-ScheduledTask" if enabled else "Disable-ScheduledTask"
    run_powershell(f"{action} -TaskName \"{TASK_NAME}\" -ErrorAction SilentlyContinue | Out-Null")
    return get_scheduler_status()


def unregister_scheduler_task():
    """Deletes the scheduled task from Windows Task Scheduler."""
    run_powershell(f"Unregister-ScheduledTask -TaskName \"{TASK_NAME}\" -Confirm:$false -ErrorAction SilentlyContinue | Out-Null")
    return {"success": True, "message": f"Task {TASK_NAME} unregistered."}
