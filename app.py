import os
import hmac
import secrets
import threading
from functools import wraps
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import run_full_audit
from database.database import (
    init_db,
    save_scan_results,
    get_scan_history,
    get_patch_history,
    get_pinned_packages
)
import security.patcher as patcher
import psutil

app = Flask(__name__)
CORS(app)

# Synchronization lock for scan progress and latest scan state
STATE_LOCK = threading.Lock()

# API Authentication configuration
DEFIANT_API_KEY = os.getenv("DEFIANT_API_KEY", "").strip()
if not DEFIANT_API_KEY:
    ACTIVE_API_KEY = secrets.token_urlsafe(32)
    print(f"[SECURITY] Generated ephemeral DEFIANT_API_KEY: {ACTIVE_API_KEY}")
else:
    ACTIVE_API_KEY = DEFIANT_API_KEY

def require_auth(f):
    """Decorator to require valid API key in X-Defiant-Key or Authorization header."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_key = request.headers.get("X-Defiant-Key")
        if not client_key:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                client_key = auth_header[7:].strip()

        if not client_key or not hmac.compare_digest(str(client_key), str(ACTIVE_API_KEY)):
            return jsonify({
                "success": False,
                "error": "Unauthorized: Valid API key required in X-Defiant-Key or Authorization header"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Store latest results in memory for the frontend
LATEST_SCAN = {
    "system_info": None,
    "score_data": None,
    "findings": []
}

SCAN_PROGRESS = {
    "status": "idle",
    "message": "",
    "percentage": 0
}

PATCHER_PROGRESS = {
    "status": "idle",
    "message": "",
    "percentage": 0,
    "current_package": ""
}

@app.route('/')
def index():
    """Renders the main dashboard."""
    return render_template('dashboard.html', api_key=ACTIVE_API_KEY)

@app.route('/api/scan/progress', methods=['GET'])
def progress():
    """Returns the current progress of the scan."""
    with STATE_LOCK:
        return jsonify(dict(SCAN_PROGRESS))

@app.route('/api/scan', methods=['POST'])
def scan():
    """Triggers a full security audit and saves results."""
    global LATEST_SCAN
    global SCAN_PROGRESS
    
    with STATE_LOCK:
        if SCAN_PROGRESS["status"] == "running":
            return jsonify({
                "success": False,
                "error": "A security scan is already in progress. Please wait for it to complete."
            }), 409
        
        SCAN_PROGRESS["status"] = "running"
        SCAN_PROGRESS["message"] = "Starting audit..."
        SCAN_PROGRESS["percentage"] = 0
    
    try:
        # We need to pass SCAN_PROGRESS to run_full_audit so it can update it
        sys_info, score, findings, _ = run_full_audit(progress_tracker=SCAN_PROGRESS)
        
        # Save to SQLite
        scan_id = save_scan_results(sys_info, score, findings)
        
        from modules.compliance import generate_compliance_report
        compliance_report = generate_compliance_report(findings)
        
        with STATE_LOCK:
            LATEST_SCAN["system_info"] = sys_info
            LATEST_SCAN["score_data"] = score
            LATEST_SCAN["findings"] = findings
            SCAN_PROGRESS["status"] = "idle"
            SCAN_PROGRESS["percentage"] = 100
            SCAN_PROGRESS["message"] = "Complete!"
        
        return jsonify({
            "success": True, 
            "scan_id": scan_id, 
            "score": score, 
            "findings": findings,
            "system_info": sys_info,
            "compliance": compliance_report
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        with STATE_LOCK:
            SCAN_PROGRESS["status"] = "error"
            SCAN_PROGRESS["message"] = f"Error: {str(e)}"
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/remediate/preview', methods=['POST'])
def remediate_preview():
    data = request.json
    from security.remediation import get_remediation_preview
    return jsonify(get_remediation_preview(data.get("finding_id")))

@app.route('/api/remediate/execute', methods=['POST'])
@require_auth
def remediate_execute():
    data = request.json
    from security.remediation import execute_remediation
    result = execute_remediation(
        finding_id=data.get("finding_id"),
        approval_granted=data.get("approval_granted", False),
        safe_only_policy=data.get("safe_only_policy", False)
    )
    return jsonify(result)

@app.route('/api/remediate/rollback', methods=['POST'])
@require_auth
def remediate_rollback():
    data = request.json
    from security.remediation import rollback_remediation
    return jsonify(rollback_remediation(data.get("finding_id")))

@app.route('/api/remediate/history', methods=['GET'])
def remediate_history():
    from security.remediation import get_remediation_history
    return jsonify({"success": True, "history": get_remediation_history()})

@app.route('/api/fim/reset', methods=['POST'])
@require_auth
def reset_fim():
    """Resets FIM baselines after an authorized change."""
    try:
        from database.database import reset_fim_baselines
        count = reset_fim_baselines()
        return jsonify({"success": True, "message": f"FIM baselines have been reset ({count} entries cleared). Run a scan to establish new baselines."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def history():
    """Returns past scan history from the database."""
    try:
        scans = get_scan_history()
        return jsonify({"success": True, "history": scans})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/telemetry', methods=['GET'])
def telemetry():
    """Returns live CPU and RAM telemetry."""
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        from database.database import save_telemetry
        save_telemetry(cpu, mem.percent)
        
        return jsonify({
            "success": True,
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/shutdown', methods=['POST'])
@require_auth
def shutdown():
    """Shuts down the backend server."""
    import signal
    os.kill(os.getpid(), signal.SIGINT)
    return jsonify({"success": True, "message": "Server shutting down..."})

# ==========================================
# Automated Patch Management API Endpoints
# ==========================================

@app.route('/api/patcher/status', methods=['GET'])
def patcher_status():
    """Returns patcher status, winget availability, scheduler status, and updatable packages."""
    try:
        winget_ok = patcher.is_winget_available()
        sched_status = patcher.get_scheduler_status()

        with STATE_LOCK:
            is_running = (PATCHER_PROGRESS["status"] == "running")

        updatables = []
        if winget_ok:
            pkg_data = patcher.get_updatable_packages()
            updatables = pkg_data.get("packages", [])

        pinned_pkgs = get_pinned_packages()

        return jsonify({
            "success": True,
            "winget_available": winget_ok,
            "bootstrap_command": None if winget_ok else patcher.get_winget_bootstrap_command(),
            "scheduler": sched_status,
            "updatable_packages": updatables,
            "updatable_count": len(updatables),
            "pinned_count": len(pinned_pkgs),
            "is_running": is_running
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/patcher/schedule', methods=['POST'])
@require_auth
def patcher_schedule():
    """Toggles or configures the automated bi-weekly scheduled task."""
    try:
        data = request.json or {}
        enabled = data.get("enabled", True)
        updated_status = patcher.toggle_scheduler_task(enabled=enabled)
        return jsonify({
            "success": True,
            "scheduler": updated_status,
            "message": f"Bi-weekly patch schedule {'enabled' if enabled else 'disabled'}."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/patcher/run-now', methods=['POST'])
@require_auth
def patcher_run_now():
    """Triggers an on-demand unattended package upgrade cycle in the background."""
    global PATCHER_PROGRESS
    with STATE_LOCK:
        if PATCHER_PROGRESS["status"] == "running":
            return jsonify({
                "success": False,
                "error": "A patch upgrade cycle is already in progress. Please wait for it to complete."
            }), 409

        PATCHER_PROGRESS["status"] = "running"
        PATCHER_PROGRESS["message"] = "Starting automated patch upgrade cycle..."
        PATCHER_PROGRESS["percentage"] = 0
        PATCHER_PROGRESS["current_package"] = ""

    def progress_callback(msg, pct):
        with STATE_LOCK:
            PATCHER_PROGRESS["message"] = msg
            PATCHER_PROGRESS["percentage"] = pct
            if "(" in msg and ")" in msg:
                PATCHER_PROGRESS["current_package"] = msg

    def background_worker():
        try:
            patcher.execute_upgrades(trigger_type="MANUAL", progress_callback=progress_callback)
        except Exception as e:
            with STATE_LOCK:
                PATCHER_PROGRESS["message"] = f"Error during patch cycle: {str(e)}"
        finally:
            with STATE_LOCK:
                PATCHER_PROGRESS["status"] = "idle"
                PATCHER_PROGRESS["percentage"] = 100

    worker_thread = threading.Thread(target=background_worker, daemon=True)
    worker_thread.start()

    return jsonify({
        "success": True,
        "message": "Automated patch upgrade cycle initiated."
    })


@app.route('/api/patcher/progress', methods=['GET'])
def patcher_progress():
    """Returns the current progress of the in-flight patch upgrade."""
    with STATE_LOCK:
        return jsonify(dict(PATCHER_PROGRESS))


@app.route('/api/patcher/pins', methods=['GET'])
def patcher_pins():
    """Returns all pinned software and recommended pins."""
    try:
        pins = patcher.get_pins()
        recommended = patcher.get_recommended_pins()
        return jsonify({
            "success": True,
            "pins": pins,
            "recommended": recommended
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/patcher/pin', methods=['POST'])
@require_auth
def patcher_add_pin():
    """Pins an application to block automated upgrades."""
    try:
        data = request.json or {}
        pkg_id = data.get("package_id")
        pkg_name = data.get("package_name")
        reason = data.get("reason")
        if not pkg_id:
            return jsonify({"success": False, "error": "package_id is required."}), 400
        result = patcher.pin_package(package_id=pkg_id, package_name=pkg_name, reason=reason)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/patcher/pin/<package_id>', methods=['DELETE'])
@require_auth
def patcher_remove_pin(package_id):
    """Unpins an application to resume automated upgrades."""
    try:
        result = patcher.unpin_package(package_id=package_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/patcher/history', methods=['GET'])
def patcher_history():
    """Returns patch execution audit history."""
    try:
        history = get_patch_history()
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Ensure database is ready
    init_db()
    
    import threading
    import webbrowser
    
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")
        
    threading.Timer(1.5, open_browser).start()
    
    # Run the web server (debug must be False in production to prevent dual-reloads)
    print("Starting Windows Security Audit Dashboard on http://127.0.0.1:5000")
    app.run(debug=False, port=5000, host="127.0.0.1")
