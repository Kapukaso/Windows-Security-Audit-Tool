# API Reference

The Defiant Windows Security Posture Platform exposes a RESTful API powered by Flask. This API serves the frontend web dashboard, allowing it to asynchronously request scans, fetch history, and monitor live telemetry.

## Base URL
All API endpoints are served from the local Flask server, typically running at:
`http://127.0.0.1:5000`

---

## 1. Trigger Full Audit
Executes the full 10-phase security audit across the host system and returns the aggregated results. The results are also automatically saved to the SQLite database.

**Endpoint:** `/api/scan`
**Method:** `POST`

### Request Body
*None required.*

### Response (JSON)
* `success` (boolean): Indicates if the scan completed without fatal errors.
* `scan_id` (integer): The primary key ID of the scan saved in the `audit_history.db` database.
* `score` (object): Contains the calculated security score.
  * `category_scores` (object): Breakdown of points earned per category.
  * `total_earned` (integer): Total points earned.
  * `total_possible` (integer): Maximum possible points (typically 135).
* `findings` (array): A list of finding objects (vulnerabilities or informational flags).
  * `id` (string): The unique finding ID (e.g., `POL-001`).
  * `category` (string): The category of the finding (e.g., `Password Policy`).
  * `severity` (string): `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `INFO`.
  * `title` (string): Description of the finding.
* `system_info` (object): Basic host information (Hostname, OS, OS Version).

---

## 2. Apply Remediation
Triggers the automated hardening script for a specific finding ID.

**Endpoint:** `/api/remediate`
**Method:** `POST`

### Request Body (JSON)
* `finding_id` (string): **Required.** The unique ID of the finding to remediate (e.g., `"POL-001"`).

```json
{
  "finding_id": "POL-001"
}
```

### Response (JSON)
* `success` (boolean): Indicates if the remediation action was successfully applied.
* `message` (string): A descriptive result message (e.g., "Successfully increased minimum password length to 8." or an error explaining why it failed).

---

## 3. Get Scan History
Retrieves the 10 most recent historical scans from the SQLite database.

**Endpoint:** `/api/history`
**Method:** `GET`

### Request Body
*None required.*

### Response (JSON)
* `success` (boolean): Indicates if the history was successfully retrieved.
* `history` (array): A list of the 10 most recent scan objects.
  * `id` (integer): The scan ID in the database.
  * `timestamp` (string): ISO 8601 formatted timestamp of when the scan occurred.
  * `hostname` (string): The host scanned.
  * `total_earned` (integer): Total points earned.
  * `total_possible` (integer): Total possible points.
  * `percentage` (float): The overall score percentage (out of 100).

---

## 4. Get Live Telemetry
Returns real-time hardware telemetry utilizing the `psutil` library. Used to drive the live CPU and RAM usage charts on the dashboard.

**Endpoint:** `/api/telemetry`
**Method:** `GET`

### Request Body
*None required.*

### Response (JSON)
* `success` (boolean): True if telemetry was successfully retrieved.
* `cpu_percent` (float): Current CPU usage percentage.
* `ram_percent` (float): Current physical memory usage percentage.
* `ram_used_gb` (float): Amount of RAM in use (in Gigabytes).
* `ram_total_gb` (float): Total physical RAM installed (in Gigabytes).
