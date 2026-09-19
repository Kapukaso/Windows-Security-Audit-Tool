"""
database/database.py
Manages SQLite database connections and schema for storing scan history.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "audit_history.db"

def init_db():
    """
    Initializes the SQLite database and creates necessary tables if they don't exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create Scans table
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
    
    # Create Findings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER,
        finding_id TEXT,
        category TEXT,
        severity TEXT,
        title TEXT,
        FOREIGN KEY(scan_id) REFERENCES scans(id)
    )
    ''')
    
    # Create Telemetry table for ML baseline
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetry_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        cpu_percent REAL,
        ram_percent REAL
    )
    ''')
    
    conn.commit()
    conn.close()

def save_telemetry(cpu_percent, ram_percent):
    """Saves CPU and RAM telemetry to the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO telemetry_log (timestamp, cpu_percent, ram_percent)
        VALUES (?, ?, ?)
    ''', (timestamp, cpu_percent, ram_percent))
    conn.commit()
    conn.close()

def get_telemetry_baseline(limit=200):
    """Retrieves recent telemetry data for ML baseline."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cpu_percent, ram_percent
        FROM telemetry_log
        ORDER BY id DESC LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_scan_results(system_info, score_data, all_findings):
    """
    Saves a completed scan and its findings into the database.
    """
    # Ensure DB is initialized
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Insert the main scan record
    timestamp = datetime.now().isoformat()
    # Handle both string arrays (legacy) and dicts for system_info
    hostname = "Unknown"
    if isinstance(system_info, dict):
        hostname = system_info.get("Hostname", "Unknown")
        
    total_earned = score_data.get("total_earned", 0)
    total_possible = score_data.get("total_possible", 100)
    percentage = (total_earned / total_possible) * 100 if total_possible > 0 else 0
    
    cursor.execute('''
        INSERT INTO scans (timestamp, hostname, total_earned, total_possible, percentage)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, hostname, total_earned, total_possible, percentage))
    
    scan_id = cursor.lastrowid
    
    # 2. Insert all findings linked to this scan
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
        cursor.executemany('''
            INSERT INTO findings (scan_id, finding_id, category, severity, title)
            VALUES (?, ?, ?, ?, ?)
        ''', findings_data)
        
    conn.commit()
    conn.close()
    
    return scan_id

def get_scan_history():
    """
    Retrieves the 10 most recent scans from the database.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
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
            "timestamp": r["timestamp"],
            "hostname": r["hostname"],
            "total_earned": r["total_earned"],
            "total_possible": r["total_possible"],
            "percentage": round(r["percentage"], 1)
        })
    return history
