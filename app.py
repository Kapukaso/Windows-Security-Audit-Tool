import os
import hmac
import secrets
import threading
from functools import wraps
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import run_full_audit
from database.database import init_db, save_scan_results, get_scan_history
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
