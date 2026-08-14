# Phase 13: Database & Persistence

## 13.1 Academic Overview
To track security posture improvements (or regressions) over time, the platform requires persistent storage. Phase 13 implements a local, serverless relational database.

## 13.2 Schema & Implementation
Uses Python's native `sqlite3` library. The schema adheres to First Normal Form (1NF) with a One-to-Many relational structure.

1. **Table: `scans` (Parent)**
   - `id` (Primary Key)
   - `timestamp` (ISO-8601)
   - `hostname`
   - `total_earned` / `percentage`

2. **Table: `findings` (Child)**
   - `id` (Primary Key)
   - `scan_id` (Foreign Key referencing `scans.id`)
   - `finding_id` (e.g., "POL-001")
   - `severity`

This architecture allows the Web Dashboard (Phase 14) to run complex SQL queries, such as fetching the last 10 scans (`ORDER BY id DESC LIMIT 10`) to render the history datatable in milliseconds.
