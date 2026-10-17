# API Reference

The Defiant Windows Security Posture Platform exposes a RESTful API powered by Flask. This API serves the frontend web dashboard and external management clients, allowing clients to trigger scans, track progress, review compliance, execute reversible hardening actions, and monitor live hardware telemetry.

## Base URL
All API endpoints are served from the local Flask server, running by default at:
`http://127.0.0.1:5000`

---

## Authentication & Security

Host-mutating endpoints are guarded by the `@require_auth` decorator. If `DEFIANT_API_KEY` is configured in `.env`, all mutating endpoints require a matching key. If unset, an ephemeral 32-byte cryptographically secure token is generated at server startup and automatically provided to the web dashboard.

### Authentication Headers
Clients can authenticate by passing the token in either of the following headers:
* `X-Defiant-Key: <your-token>`
* `Authorization: Bearer <your-token>`

Tokens are compared using constant-time evaluation (`hmac.compare_digest`) to prevent timing attacks.

### Protected Endpoints
* `POST /api/remediate/execute`
* `POST /api/remediate/rollback`
* `POST /api/fim/reset`
* `POST /api/shutdown`

---

## Endpoints

### 1. Trigger Full Audit
Triggers a multi-threaded security audit across all 16 host collection modules, computes risk scores, compiles multi-standard compliance reports, and records the results to the database.

* **Endpoint:** `/api/scan`
* **Method:** `POST`
* **Auth Required:** No

#### Response (`200 OK`)
```json
{
  "success": true,
  "scan_id": 17,
  "score": {
    "total_earned": 140,
    "total_possible": 190,
    "percentage": 73.68,
    "category_scores": {
      "Defender": 25,
      "Firewall": 25,
      "Users": 10,
      "Password Policy": 15,
      "Installed Software": 15,
      "Running Services": 10,
      "Startup Applications": 5,
      "Network Ports": 10,
      "Windows Updates": 15,
      "Event Logs": 10,
      "File Integrity Monitoring": 10,
      "Machine Learning Anomalies": 10,
      "Registry & Drivers": 30
    }
  },
  "compliance": {
    "CIS": {
      "compliance_score": 80.0,
      "passed": 8,
      "failed": 2,
      "rules": [
        {
          "requirement": "CIS 2.1 (UAC Settings)",
          "description": "Ensure User Account Control (UAC) is enabled.",
          "status": "PASS",
          "evidence": "System meets secure baseline configuration.",
          "fix_guidance": "Maintain current configuration."
        }
      ]
    },
    "NIST_SP_800_53": { "compliance_score": 85.0, "passed": 17, "failed": 3 },
    "ISO_27001": { "compliance_score": 90.0, "passed": 9, "failed": 1 },
    "HIPAA": { "compliance_score": 88.0, "passed": 7, "failed": 1 }
  },
  "system_info": {
    "Computer Name": "DESKTOP-MNP9GR1",
    "Operating System": "Windows",
    "OS Version": "10.0.26100",
    "Architecture": "AMD64",
    "RAM (GB)": 15.71,
    "CPU Usage (%)": 12.5
  },
  "findings": [
    {
      "id": "REG-001",
      "category": "Registry & Drivers",
      "severity": "HIGH",
      "title": "LSA RunAsPPL is not enabled",
      "description": "Local Security Authority is running without Protected Process Light protection.",
      "recommendation": "Enable RunAsPPL in HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa."
    }
  ]
}
```

*Note: If an audit is already running when this endpoint is called, it returns `409 Conflict` with `{"success": false, "error": "A security scan is already in progress."}`.*

---

### 2. Poll Scan Progress
Retrieves real-time execution status and task completion percentage during an audit.

* **Endpoint:** `/api/scan/progress`
* **Method:** `GET`
* **Auth Required:** No

#### Response (`200 OK`)
```json
{
  "status": "running",
  "message": "Completed firewall scan...",
  "percentage": 45
}
```

---

### 3. Preview Remediation Playbook
Retrieves detailed impact analysis, risk classification, exact PowerShell/cmd execution commands, and verification procedures before executing a fix.

* **Endpoint:** `/api/remediate/preview`
* **Method:** `POST`
* **Auth Required:** No

#### Request Body
```json
{
  "finding_id": "REG-001"
}
```

#### Response (`200 OK`)
```json
{
  "finding_id": "REG-001",
  "title": "Enable LSA Protection (RunAsPPL)",
  "description": "Enables LSASS Protected Process Light to defend against memory extraction tools like Mimikatz.",
  "command": "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name 'RunAsPPL' -Value 1 -Type DWord -Force",
  "rollback_cmd": "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa' -Name 'RunAsPPL' -Value 0 -Type DWord -Force",
  "safe_only": false,
  "requires_approval": true,
  "impact": "HIGH"
}
```

---

### 4. Execute Remediation Playbook
Executes a remediation playbook to harden the system against a detected vulnerability.

* **Endpoint:** `/api/remediate/execute`
* **Method:** `POST`
* **Auth Required:** Yes (`X-Defiant-Key` or `Authorization: Bearer`)

#### Request Body
```json
{
  "finding_id": "REG-001",
  "approval_granted": true,
  "safe_only_policy": false
}
```

#### Response (`200 OK`)
```json
{
  "finding_id": "REG-001",
  "status": "SUCCESS",
  "message": "Successfully enabled LSA Protection (RunAsPPL).",
  "verification_passed": true
}
```

#### Error Responses
* `401 Unauthorized`: Missing or invalid authentication token.
* `200 OK` with status `"BLOCKED"`: If `requires_approval` is true but `approval_granted` is false, or if `safe_only_policy` is true and the playbook is classified as non-safe.

---

### 5. Rollback Remediation
Executes the registered reverse command for a previously applied remediation to restore prior system state.

* **Endpoint:** `/api/remediate/rollback`
* **Method:** `POST`
* **Auth Required:** Yes (`X-Defiant-Key` or `Authorization: Bearer`)

#### Request Body
```json
{
  "finding_id": "REG-001"
}
```

#### Response (`200 OK`)
```json
{
  "finding_id": "REG-001",
  "status": "SUCCESS",
  "message": "Successfully rolled back finding REG-001."
}
```

---

### 6. Get Remediation Audit History
Retrieves all historical remediation execution and rollback records from the database.

* **Endpoint:** `/api/remediate/history`
* **Method:** `GET`
* **Auth Required:** No

#### Response (`200 OK`)
```json
{
  "success": true,
  "history": [
    {
      "id": 1,
      "timestamp": "2026-10-17T15:30:00",
      "finding_id": "REG-001",
      "action_type": "EXECUTE",
      "status": "SUCCESS",
      "message": "Successfully enabled LSA Protection (RunAsPPL)."
    }
  ]
}
```

---

### 7. Reset File Integrity Monitoring (FIM) Baselines
Clears existing cryptographic file baselines from the database. Subsequent scans will calculate and record a fresh baseline.

* **Endpoint:** `/api/fim/reset`
* **Method:** `POST`
* **Auth Required:** Yes (`X-Defiant-Key` or `Authorization: Bearer`)

#### Response (`200 OK`)
```json
{
  "success": true,
  "message": "FIM baselines have been reset (4 entries cleared). Run a scan to establish new baselines."
}
```

---

### 8. Get Scan History
Retrieves historical security posture scans and score trends from the database.

* **Endpoint:** `/api/history`
* **Method:** `GET`
* **Auth Required:** No

#### Response (`200 OK`)
```json
{
  "success": true,
  "history": [
    {
      "id": 17,
      "timestamp": "2026-10-17T16:29:20",
      "hostname": "DESKTOP-MNP9GR1",
      "total_earned": 140,
      "total_possible": 190,
      "percentage": 73.68
    }
  ]
}
```

---

### 9. Get Live Hardware Telemetry
Fetches real-time CPU and RAM utilization metrics via `psutil` and records entries into the database telemetry log.

* **Endpoint:** `/api/telemetry`
* **Method:** `GET`
* **Auth Required:** No

#### Response (`200 OK`)
```json
{
  "success": true,
  "cpu_percent": 14.2,
  "ram_percent": 68.5,
  "ram_used_gb": 10.76,
  "ram_total_gb": 15.71
}
```

---

### 10. Shutdown Server
Gracefully terminates the Flask background web service.

* **Endpoint:** `/api/shutdown`
* **Method:** `POST`
* **Auth Required:** Yes (`X-Defiant-Key` or `Authorization: Bearer`)

#### Response (`200 OK`)
```json
{
  "success": true,
  "message": "Server shutting down..."
}
```
