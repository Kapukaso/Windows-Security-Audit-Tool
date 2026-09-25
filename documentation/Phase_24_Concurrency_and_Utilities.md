# Phase 24: Concurrency & Utilities

## 24.1 Overview
As the Defiant platform evolved to include highly intensive audits (such as real-time CVE database lookups, File Integrity Monitoring over large binaries, and extensive Machine Learning tasks), the sequential audit loop introduced severe performance bottlenecks. Phase 24 addresses this by introducing multi-threading (concurrency) for independent data collection modules and formalizing the `utils/` library for safe OS-level interactions.

## 24.2 Asynchronous Audit Execution
The core audit logic in `main.py` (`run_full_audit`) was rewritten to leverage Python's `concurrent.futures.ThreadPoolExecutor`. 

*   **Parallel Collection**: Standard data collection modules (e.g., Firewall, Windows Defender, Local Users, Running Services) are dispatched to a pool of up to 10 background worker threads.
*   **Non-Blocking I/O**: Because the majority of these modules rely on I/O-bound OS queries (WMI, PowerShell, Registry Reads), multi-threading yields a massive performance increase by allowing the system to wait on multiple OS responses simultaneously.
*   **Real-Time Progress Streaming**: A `progress_tracker` object was introduced to track the state of the thread pool. The `app.py` server exposes this via the `/api/scan/progress` endpoint, allowing the UI to display a live percentage and status message instead of blocking the browser window.

## 24.3 Utilities (`utils/`)
To prevent code duplication across the audit modules, a centralized `utils/` package was standardized:

*   **`powershell.py`**: A secure wrapper for `subprocess.run()`. It ensures that PowerShell commands are executed non-interactively with correct character encoding and error suppression. The `run_powershell_json` function enforces structured data returns, mitigating the brittleness of traditional regex parsing.
*   **`display.py`**: Contains helper functions for rendering the raw audit data into CLI tables using the `tabulate` library.
*   **`logger.py`**: Centralized logging logic.
*   **`constants.py`**: Stores global system constants to prevent hardcoded magic strings across the codebase.
