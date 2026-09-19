# Phase 17: Machine Learning Anomaly Detection

## 17.1 Academic Overview & Motivation
Traditional vulnerability auditing is highly deterministic: it looks for known bad configurations. However, active threats (like cryptojackers or ransomware) generate anomalous behavioral footprints. Phase 17 introduces an Unsupervised Machine Learning model to evaluate the systemic behavior of the endpoint in real-time.

This maps directly to **CIS Control 8: Audit Log Management and Anomaly Detection**.

## 17.2 Technical Implementation (Isolation Forest)
The platform integrates the `scikit-learn` Machine Learning library. Because ransomware and cryptominers drastically alter the I/O and CPU utilization of a machine, the platform trains an **Isolation Forest** model to detect outliers.

### Why Isolation Forest?
Unlike clustering algorithms (like K-Means), the Isolation Forest algorithm explicitly builds decision trees to isolate anomalies. It is mathematically optimized for outlier detection, making it lightweight enough to run locally on an endpoint without sending telemetry to a cloud server.

```python
from sklearn.ensemble import IsolationForest
import psutil
import numpy as np

# Train on baseline telemetry
baseline = np.column_stack((normal_cpu, normal_ram))
model = IsolationForest(n_estimators=100, contamination=0.05)
model.fit(baseline)

# Predict current system state
current_state = np.array([[psutil.cpu_percent(), psutil.virtual_memory().percent]])
prediction = model.predict(current_state)
```

## 17.3 Vulnerability Logic
If the model returns `-1` (Anomaly Detected), the engine triggers a **HIGH** severity finding (`ML-001`). This alerts the dashboard that the endpoint is experiencing a severe systemic behavioral deviation, warranting immediate Incident Response (IR).
