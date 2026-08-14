"""
app.py
Web-based Dashboard and Hardening Platform using Flask.
"""
from flask import Flask, render_template, request, jsonify
from main import run_full_audit
from database.database import init_db, save_scan_results, get_scan_history
from security.remediation import apply_remediation
import psutil

app = Flask(__name__)

# Store latest results in memory for the frontend
LATEST_SCAN = {
    "system_info": None,
    "score_data": None,
    "findings": []
}

@app.route('/')
def index():
    """Renders the main dashboard."""
    return render_template('dashboard.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    """Triggers a full security audit and saves results."""
    global LATEST_SCAN
    
    try:
        sys_info, score, findings = run_full_audit()
        
        LATEST_SCAN["system_info"] = sys_info
        LATEST_SCAN["score_data"] = score
        LATEST_SCAN["findings"] = findings
        
        # Save to SQLite
        scan_id = save_scan_results(sys_info, score, findings)
        
        return jsonify({
            "success": True, 
            "scan_id": scan_id, 
            "score": score, 
            "findings": findings,
            "system_info": sys_info
        })
        
    except Exception as e:
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
        return jsonify({
            "success": True,
            "cpu_percent": cpu,
            "ram_percent": mem.percent,
            "ram_used_gb": round(mem.used / (1024**3), 2),
            "ram_total_gb": round(mem.total / (1024**3), 2)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Ensure database is ready
    init_db()
    
    # Run the web server
    print("Starting Windows Security Audit Dashboard on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
