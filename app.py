"""
app.py
Web-based Dashboard and Hardening Platform using Flask.
"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from main import run_full_audit
from database.database import init_db, save_scan_results, get_scan_history
from security.remediation import apply_remediation
import psutil

app = Flask(__name__)
CORS(app)

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
    return render_template('dashboard.html')

@app.route('/api/scan/progress', methods=['GET'])
def progress():
    """Returns the current progress of the scan."""
    return jsonify(SCAN_PROGRESS)

@app.route('/api/scan', methods=['POST'])
def scan():
    """Triggers a full security audit and saves results."""
    global LATEST_SCAN
    global SCAN_PROGRESS
    
    try:
        SCAN_PROGRESS["status"] = "running"
        SCAN_PROGRESS["message"] = "Starting audit..."
        SCAN_PROGRESS["percentage"] = 0
        
        # We need to pass SCAN_PROGRESS to run_full_audit so it can update it
        sys_info, score, findings, _ = run_full_audit(progress_tracker=SCAN_PROGRESS)
        
        LATEST_SCAN["system_info"] = sys_info
        LATEST_SCAN["score_data"] = score
        LATEST_SCAN["findings"] = findings
        
        # Save to SQLite
        scan_id = save_scan_results(sys_info, score, findings)
        
        SCAN_PROGRESS["status"] = "idle"
        SCAN_PROGRESS["percentage"] = 100
        SCAN_PROGRESS["message"] = "Complete!"
        
        return jsonify({
            "success": True, 
            "scan_id": scan_id, 
            "score": score, 
            "findings": findings,
            "system_info": sys_info
        })
        
    except Exception as e:
        SCAN_PROGRESS["status"] = "error"
        SCAN_PROGRESS["message"] = f"Error: {str(e)}"
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/remediate', methods=['POST'])
def remediate():
    """Applies automated hardening for a specific finding."""
    data = request.json
    finding_id = data.get("finding_id")
    
    if not finding_id:
        return jsonify({"success": False, "message": "Missing finding_id"})
        
    result = apply_remediation(finding_id)
    return jsonify(result)

@app.route('/api/fim/reset', methods=['POST'])
def reset_fim():
    """Resets FIM baselines after an authorized change."""
    try:
        import sqlite3
        from database.database import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS fim_baselines")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "FIM baselines have been reset. Run a scan to establish new baselines."})
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
def shutdown():
    """Shuts down the backend server."""
    import os, signal
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
