"""
database/database.py
Enterprise Database Connector (PostgreSQL / SQLite fallback).
"""
import os
import json
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

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.extensions
except ImportError:
    psycopg2 = None

def is_postgres(conn):
    """Checks whether the active connection is a PostgreSQL connection."""
    if psycopg2 is not None:
        try:
            if isinstance(conn, psycopg2.extensions.connection):
                return True
        except Exception:
            pass
    return type(conn).__module__.startswith("psycopg2")

def get_connection():
    """
    Returns an active database connection.
    If DB_ENGINE is postgres, attempts connection to PostgreSQL with seamless
    fallback to SQLite if PostgreSQL is unreachable.
    """
    if DB_ENGINE == "postgres" and psycopg2 is not None:
        try:
            return psycopg2.connect(PG_URL)
        except Exception as e:
            print(f"[!] WARNING: Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")
            return sqlite3.connect(SQLITE_PATH)
    return sqlite3.connect(SQLITE_PATH)

def init_db():
    """Initializes the database schema with full parity across SQLite and PostgreSQL."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if is_postgres(conn):
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fim_baselines (
            file_path TEXT PRIMARY KEY,
            sha256_hash TEXT NOT NULL,
            last_checked TIMESTAMP NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS nvd_cve_cache (
            id SERIAL PRIMARY KEY,
            software_name TEXT NOT NULL,
            software_version TEXT,
            cve_data TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fim_baselines (
            file_path TEXT PRIMARY KEY,
            sha256_hash TEXT NOT NULL,
            last_checked TEXT NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS nvd_cve_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            software_name TEXT NOT NULL,
            software_version TEXT,
            cve_data TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        ''')

    # Create Indexes for high-speed lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_findings_scan_id ON findings(scan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry_log(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fim_path ON fim_baselines(file_path)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cve_lookup ON nvd_cve_cache(software_name, software_version)')
    
    conn.commit()
    conn.close()

def maintain_database(retention_days=7, max_scans=100):
    """Prunes stale telemetry, old scan findings, and expired CVE cache records."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if is_postgres(conn):
            cursor.execute(f"DELETE FROM telemetry_log WHERE timestamp < NOW() - INTERVAL '{retention_days} days'")
            cursor.execute(f"DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT {max_scans})")
            cursor.execute("DELETE FROM findings WHERE scan_id NOT IN (SELECT id FROM scans)")
            cursor.execute("DELETE FROM nvd_cve_cache WHERE timestamp < NOW() - INTERVAL '30 days'")
        else:
            cursor.execute(f"DELETE FROM telemetry_log WHERE timestamp < datetime('now', '-{retention_days} days')")
            cursor.execute(f"DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT {max_scans})")
            cursor.execute("DELETE FROM findings WHERE scan_id NOT IN (SELECT id FROM scans)")
            cursor.execute("DELETE FROM nvd_cve_cache WHERE timestamp < datetime('now', '-30 days')")
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
    
    try:
        if is_postgres(conn):
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
    finally:
        conn.close()

def get_telemetry_baseline(limit=200):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = f"SELECT cpu_percent, ram_percent FROM telemetry_log ORDER BY id DESC LIMIT {limit}"
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    finally:
        conn.close()

def save_scan_results(system_info, score_data, all_findings):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    hostname = system_info.get("Hostname", "Unknown") if isinstance(system_info, dict) else "Unknown"
    total_earned = score_data.get("total_earned", 0)
    total_possible = score_data.get("total_possible", 100)
    percentage = (total_earned / total_possible) * 100 if total_possible > 0 else 0
    
    try:
        if is_postgres(conn):
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
            if is_postgres(conn):
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
    finally:
        conn.close()
    
    maintain_database()
    return scan_id

def get_scan_history():
    init_db()
    conn = get_connection()
    try:
        if is_postgres(conn):
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
    finally:
        conn.close()

# ==============================================================================
# FIM (File Integrity Monitoring) DAO Helpers
# ==============================================================================

def get_fim_baseline(file_path):
    """Returns the recorded SHA-256 hash for a given file path, or None if unbaselined."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if is_postgres(conn):
            cursor.execute("SELECT sha256_hash FROM fim_baselines WHERE file_path = %s", (file_path,))
        else:
            cursor.execute("SELECT sha256_hash FROM fim_baselines WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def save_fim_baseline(file_path, sha256_hash):
    """Establishes or updates the cryptographic hash baseline for a file path."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    try:
        if is_postgres(conn):
            cursor.execute('''
                INSERT INTO fim_baselines (file_path, sha256_hash, last_checked)
                VALUES (%s, %s, %s)
                ON CONFLICT (file_path) DO UPDATE SET
                    sha256_hash = EXCLUDED.sha256_hash,
                    last_checked = EXCLUDED.last_checked
            ''', (file_path, sha256_hash, timestamp))
        else:
            cursor.execute('''
                INSERT OR REPLACE INTO fim_baselines (file_path, sha256_hash, last_checked)
                VALUES (?, ?, ?)
            ''', (file_path, sha256_hash, timestamp))
        conn.commit()
    finally:
        conn.close()

def reset_fim_baselines():
    """
    Clears all FIM baseline records via DELETE FROM fim_baselines (D-01).
    Preserves table structure and indexes without requiring DDL DROP permissions.
    Returns the count of deleted baselines.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM fim_baselines")
        count = cursor.rowcount if cursor.rowcount >= 0 else 0
        conn.commit()
        return count
    finally:
        conn.close()

# ==============================================================================
# CVE Cache DAO Helpers (NIST NVD)
# ==============================================================================

def get_cve_cache(software_name, software_version=None, max_age_days=7):
    """
    Retrieves cached CVE JSON data if recorded within max_age_days (D-03).
    Returns parsed list/dict or None if not cached or expired.
    """
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if is_postgres(conn):
            if software_version:
                cursor.execute(f'''
                    SELECT cve_data FROM nvd_cve_cache
                    WHERE LOWER(software_name) = LOWER(%s)
                      AND LOWER(software_version) = LOWER(%s)
                      AND timestamp >= NOW() - INTERVAL '{max_age_days} days'
                    ORDER BY id DESC LIMIT 1
                ''', (software_name, software_version))
            else:
                cursor.execute(f'''
                    SELECT cve_data FROM nvd_cve_cache
                    WHERE LOWER(software_name) = LOWER(%s)
                      AND (software_version IS NULL OR software_version = '')
                      AND timestamp >= NOW() - INTERVAL '{max_age_days} days'
                    ORDER BY id DESC LIMIT 1
                ''', (software_name,))
        else:
            if software_version:
                cursor.execute(f'''
                    SELECT cve_data FROM nvd_cve_cache
                    WHERE LOWER(software_name) = LOWER(?)
                      AND LOWER(software_version) = LOWER(?)
                      AND timestamp >= datetime('now', '-{max_age_days} days')
                    ORDER BY id DESC LIMIT 1
                ''', (software_name, software_version))
            else:
                cursor.execute(f'''
                    SELECT cve_data FROM nvd_cve_cache
                    WHERE LOWER(software_name) = LOWER(?)
                      AND (software_version IS NULL OR software_version = '')
                      AND timestamp >= datetime('now', '-{max_age_days} days')
                    ORDER BY id DESC LIMIT 1
                ''', (software_name,))
                
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except Exception:
                return row[0]
        return None
    finally:
        conn.close()

def save_cve_cache(software_name, software_version, cve_data):
    """Stores CVE JSON data in nvd_cve_cache (D-03)."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    payload = json.dumps(cve_data) if not isinstance(cve_data, str) else cve_data
    
    try:
        if is_postgres(conn):
            cursor.execute('''
                INSERT INTO nvd_cve_cache (software_name, software_version, cve_data, timestamp)
                VALUES (%s, %s, %s, %s)
            ''', (software_name, software_version, payload, timestamp))
        else:
            cursor.execute('''
                INSERT INTO nvd_cve_cache (software_name, software_version, cve_data, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (software_name, software_version, payload, timestamp))
        conn.commit()
    finally:
        conn.close()
