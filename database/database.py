"""
database/database.py
Enterprise Database Connector (PostgreSQL / SQLite fallback).
"""
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration from Environment Variables
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
PG_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/defiant")
SQLITE_PATH = "audit_history.db"

# Backward compatibility for FIM modules which track states locally
DB_PATH = SQLITE_PATH

if DB_ENGINE == "postgres":
    import psycopg2
    import psycopg2.extras

def get_connection():
    if DB_ENGINE == "postgres":
        return psycopg2.connect(PG_URL)
    return sqlite3.connect(SQLITE_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    if DB_ENGINE == "postgres":
        # PostgreSQL Schema (Enterprise)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            hostname TEXT NOT NULL,
            total_earned INTEGER,
            total_possible INTEGER,
            percentage REAL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id SERIAL PRIMARY KEY,
            scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
            finding_id TEXT,
            category TEXT,
            severity TEXT,
            title TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_log (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            cpu_percent REAL,
            ram_percent REAL
        )
        ''')
    else:
        # SQLite Schema (Local Fallback)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hostname TEXT NOT NULL,
            total_earned INTEGER,
            total_possible INTEGER,
            percentage REAL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            finding_id TEXT,
            category TEXT,
            severity TEXT,
            title TEXT,
            FOREIGN KEY(scan_id) REFERENCES scans(id) ON DELETE CASCADE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetry_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_percent REAL,
            ram_percent REAL
        )
        ''')

    # Create Indexes for high-speed lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON findings(scan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_log(timestamp)')
    
    conn.commit()
    conn.close()

def maintain_database(retention_days=7, max_scans=100):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if DB_ENGINE == "postgres":
            cursor.execute(f"DELETE FROM telemetry_log WHERE timestamp < NOW() - INTERVAL '{retention_days} days'")
            cursor.execute(f"DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT {max_scans})")
            cursor.execute("DELETE FROM findings WHERE scan_id NOT IN (SELECT id FROM scans)")
            # VACUUM cannot be run inside a transaction block in Postgres, skip for now.
        else:
            cursor.execute(f"DELETE FROM telemetry_log WHERE timestamp < datetime('now', '-{retention_days} days')")
            cursor.execute(f"DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT {max_scans})")
            cursor.execute("DELETE FROM findings WHERE scan_id NOT IN (SELECT id FROM scans)")
            cursor.execute("VACUUM")
            
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_telemetry(cpu_percent, ram_percent):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    if DB_ENGINE == "postgres":
        cursor.execute('''
            INSERT INTO telemetry_log (timestamp, cpu_percent, ram_percent)
            VALUES (%s, %s, %s)
        ''', (timestamp, cpu_percent, ram_percent))
    else:
        cursor.execute('''
            INSERT INTO telemetry_log (timestamp, cpu_percent, ram_percent)
            VALUES (?, ?, ?)
        ''', (timestamp, cpu_percent, ram_percent))
        
    conn.commit()
    conn.close()

def get_telemetry_baseline(limit=200):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    query = f"SELECT cpu_percent, ram_percent FROM telemetry_log ORDER BY id DESC LIMIT {limit}"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_scan_results(system_info, score_data, all_findings):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    hostname = system_info.get("Hostname", "Unknown") if isinstance(system_info, dict) else "Unknown"
    total_earned = score_data.get("total_earned", 0)
    total_possible = score_data.get("total_possible", 100)
    percentage = (total_earned / total_possible) * 100 if total_possible > 0 else 0
    
    if DB_ENGINE == "postgres":
        cursor.execute('''
            INSERT INTO scans (timestamp, hostname, total_earned, total_possible, percentage)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        ''', (timestamp, hostname, total_earned, total_possible, percentage))
        scan_id = cursor.fetchone()[0]
    else:
        cursor.execute('''
            INSERT INTO scans (timestamp, hostname, total_earned, total_possible, percentage)
            VALUES (?, ?, ?, ?, ?)
        ''', (timestamp, hostname, total_earned, total_possible, percentage))
        scan_id = cursor.lastrowid
    
    findings_data = []
    for finding in all_findings:
        if isinstance(finding, dict):
            findings_data.append((
                scan_id,
                finding.get("id", "UNKNOWN"),
                finding.get("category", "Uncategorized"),
                finding.get("severity", "INFO"),
                finding.get("title", "Legacy/Unknown finding")
            ))
            
    if findings_data:
        if DB_ENGINE == "postgres":
            cursor.executemany('''
                INSERT INTO findings (scan_id, finding_id, category, severity, title)
                VALUES (%s, %s, %s, %s, %s)
            ''', findings_data)
        else:
            cursor.executemany('''
                INSERT INTO findings (scan_id, finding_id, category, severity, title)
                VALUES (?, ?, ?, ?, ?)
            ''', findings_data)
        
    conn.commit()
    conn.close()
    
    maintain_database()
    return scan_id

def get_scan_history():
    init_db()
    conn = get_connection()
    if DB_ENGINE == "postgres":
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    else:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, timestamp, hostname, total_earned, total_possible, percentage
        FROM scans
        ORDER BY id DESC LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r in rows:
        history.append({
            "id": r["id"],
            "timestamp": str(r["timestamp"]),
            "hostname": r["hostname"],
            "total_earned": r["total_earned"],
            "total_possible": r["total_possible"],
            "percentage": round(float(r["percentage"]), 1)
        })
    return history
