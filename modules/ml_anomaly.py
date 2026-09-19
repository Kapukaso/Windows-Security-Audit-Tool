"""
modules/ml_anomaly.py
Machine Learning Anomaly Detection.
Uses an Isolation Forest to detect abnormal CPU/RAM telemetry spikes.
"""
import psutil
import numpy as np
try:
    from sklearn.ensemble import IsolationForest
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def generate_training_baseline():
    """
    Fetches real system baseline data from SQLite.
    Falls back to simulated data if not enough history exists.
    Format: [CPU_Usage, RAM_Usage]
    """
    from database.database import get_telemetry_baseline
    rows = get_telemetry_baseline(limit=200)
    
    if len(rows) < 50:
        # Not enough data yet, fall back to simulation
        np.random.seed(42)
        normal_cpu = np.random.normal(15, 5, 200)
        normal_ram = np.random.normal(45, 10, 200)
        normal_cpu = np.clip(normal_cpu, 0, 100)
        normal_ram = np.clip(normal_ram, 0, 100)
        return np.column_stack((normal_cpu, normal_ram))
        
    return np.array(rows)

def audit_anomalies():
    """
    Samples current telemetry and runs it through the ML model to detect anomalies.
    """
    findings = []
    
    if not ML_AVAILABLE:
        findings.append({
            "id": "ML-ERR",
            "category": "Anomalies",
            "severity": "INFO",
            "title": "ML Engine Unavailable",
            "description": "scikit-learn is not installed. Anomaly detection skipped."
        })
        return findings

    try:
        # 1. Train the Unsupervised Model on 'Normal' baseline
        baseline_data = generate_training_baseline()
        # contamination=0.05 implies we expect 5% of future data might be anomalies
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(baseline_data)
        
        # 2. Get current system state
        current_cpu = psutil.cpu_percent(interval=1.0)
        current_ram = psutil.virtual_memory().percent
        
        current_state = np.array([[current_cpu, current_ram]])
        
        # 3. Predict (-1 is anomaly, 1 is normal)
        prediction = model.predict(current_state)
        
        if prediction[0] == -1:
            findings.append({
                "id": "ML-001",
                "category": "Anomalies",
                "severity": "HIGH",
                "title": "Behavioral Telemetry Anomaly Detected",
                "description": f"The ML Isolation Forest model flagged current system behavior (CPU: {current_cpu}%, RAM: {current_ram}%) as highly anomalous compared to historical baselines. Potential cryptojacker or runaway process."
            })
            
    except Exception as e:
        findings.append({
            "id": "ML-ERR",
            "category": "Anomalies",
            "severity": "INFO",
            "title": "ML Execution Failure",
            "description": str(e)
        })

    return findings
