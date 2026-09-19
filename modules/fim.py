"""
modules/fim.py
File Integrity Monitoring (FIM).
Monitors critical system files for unauthorized cryptographic hash changes.
"""
import hashlib
import os
import sqlite3

CRITICAL_FILES = [
    r"C:\Windows\System32\drivers\etc\hosts",
    r"C:\Windows\System32\drivers\etc\lmhosts.sam",
    r"C:\Windows\System32\sethc.exe",          # Sticky Keys hijack target
    r"C:\Windows\System32\utilman.exe",        # Utility Manager hijack
    r"C:\Windows\System32\osk.exe",            # On-screen keyboard hijack
    r"C:\Windows\System32\magnify.exe",
    r"C:\Windows\System32\cmd.exe",
    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
]

def hash_file(filepath):
    """Returns the SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return None
    
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()
    except Exception:
        return None

def audit_fim(db_path="audit_history.db"):
    """
    Checks critical files against known baselines in the database.
    If a baseline doesn't exist, it creates one.
    """
    findings = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ensure FIM table exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fim_baselines (
            file_path TEXT PRIMARY KEY,
            sha256_hash TEXT NOT NULL
        )
        ''')
        
        for filepath in CRITICAL_FILES:
            current_hash = hash_file(filepath)
            
            if not current_hash:
                findings.append({
                    "id": "FIM-002",
                    "category": "FIM",
                    "severity": "HIGH",
                    "title": f"Critical File Missing or Inaccessible",
                    "description": f"Could not hash {filepath}."
                })
                continue
            
            cursor.execute("SELECT sha256_hash FROM fim_baselines WHERE file_path = ?", (filepath,))
            row = cursor.fetchone()
            
            if row is None:
                # Baseline doesn't exist. This is the first scan. Save the baseline.
                cursor.execute("INSERT INTO fim_baselines (file_path, sha256_hash) VALUES (?, ?)", (filepath, current_hash))
                # Add an INFO finding just to note that a baseline was established.
                findings.append({
                    "id": "FIM-INFO",
                    "category": "FIM",
                    "severity": "INFO",
                    "title": f"Baseline Established",
                    "description": f"Initial SHA-256 baseline recorded for {filepath}."
                })
            else:
                baseline_hash = row[0]
                if current_hash != baseline_hash:
                    findings.append({
                        "id": "FIM-001",
                        "category": "FIM",
                        "severity": "CRITICAL",
                        "title": "File Integrity Violation",
                        "description": f"The hash for {filepath} has changed! Baseline: {baseline_hash[:8]}... Current: {current_hash[:8]}... This indicates tampering or rootkit activity."
                    })
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        findings.append({
            "id": "FIM-ERR",
            "category": "FIM",
            "severity": "MEDIUM",
            "title": "FIM Engine Failure",
            "description": str(e)
        })
        
    return findings
