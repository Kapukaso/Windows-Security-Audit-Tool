# Phase 14: Next-Generation Web Dashboard

## 14.1 Academic Overview & Motivation
An Endpoint Detection and Response (EDR) platform is useless if security analysts cannot quickly interpret its findings. Phase 14 transitions the project from a command-line interface into a fully asynchronous, Single Page Application (SPA) dashboard. 

This UI aligns with the **NIST Cybersecurity Framework (CSF) PR.AT (Awareness and Training)** by presenting vulnerabilities in a clear, human-readable format, preventing alert fatigue.

## 14.2 Technical Implementation (Glassmorphism & Chart.js)
The frontend uses a modern "Glassmorphism" aesthetic built with native CSS, eliminating heavy frontend frameworks like React to keep the executable lightweight.

### Asynchronous Fetch API
When the user clicks "Initiate Audit", the UI does not freeze. It uses JavaScript's `fetch()` API to make a non-blocking POST request to the Flask backend.

### Live Telemetry (Chart.js)
The platform streams real-time CPU and RAM metrics via a `/api/telemetry` endpoint. 
```javascript
const cpuChart = new Chart(cpuCtx, {
    type: 'line',
    data: { 
        labels: Array(20).fill(''), 
        datasets: [{ data: Array(20).fill(0), borderColor: '#00f0ff' }] 
    }
});
```
This data dynamically updates the `Chart.js` line graphs every 1.5 seconds, mimicking enterprise tools like CrowdStrike or Windows Task Manager.

## 14.3 Visual Analytics & Gamification
- **SVG Circular Gauge:** The primary risk score is rendered using a scalable Vector Graphic (SVG) circle. The `stroke-dasharray` property is dynamically calculated using JavaScript to fill the circle based on the `(total_earned / total_possible) * 100` formula.
- **Cyberpunk Color Palette:** Severity levels are mapped to specific neon hex codes (e.g., `#ff2a55` for CRITICAL) to immediately draw the analyst's eye to high-priority threats.
