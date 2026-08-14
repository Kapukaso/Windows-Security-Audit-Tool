# Phase 14: Web Dashboard & EDR Interface

## 14.1 Academic Overview
CLI tools are hostile to non-technical analysts. Phase 14 transforms the backend scripts into an Enterprise Endpoint Detection and Response (EDR) platform using modern web technologies.

## 14.2 Architecture (REST API)
The backend utilizes the **Flask** micro-framework. It binds to `127.0.0.1:5000` and serves RESTful JSON endpoints:
- `POST /api/scan`: Triggers the heavy 10-phase audit and returns the JSON payload.
- `GET /api/history`: Queries SQLite and returns historical scan data.
- `GET /api/telemetry`: Queries `psutil` and returns CPU/RAM allocation.

## 14.3 Frontend SPA (Single Page Application)
The `dashboard.html` file acts as the view layer.
- **Aesthetics:** Uses a deep `#050505` background, `lucide-icons`, and `JetBrains Mono` fonts to mimic the UI/UX of premium tools like SentinelOne or Datadog.
- **Asynchronous UX:** Vanilla JavaScript uses the `fetch()` API and `async/await` syntax to hit the Flask endpoints. It dynamically updates the DOM and the Circular Risk Gauge without ever triggering a full page reload, resulting in a highly fluid, app-like experience.
