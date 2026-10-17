"""
modules/fim.py
File Integrity Monitoring (FIM).
Monitors critical system files for unauthorized cryptographic hash changes.
"""
import hashlib
import os
from database.database import get_fim_baseline, save_fim_baseline

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

def audit_fim(db_path=None):
    """
    Checks critical files against known baselines in the database.
    If a baseline doesn't exist, it creates one.
    """
    findings = []
    
    try:
        for filepath in CRITICAL_FILES:
            current_hash = hash_file(filepath)
            
            if not current_hash:
                findings.append({
                    "id": "FIM-002",
                    "category": "FIM",
                    "severity": "HIGH",
                    "title": "Critical File Missing or Inaccessible",
                    "description": f"Could not hash {filepath}."
                })
                continue
            
            baseline_hash = get_fim_baseline(filepath)
            
            if baseline_hash is None:
                # Baseline doesn't exist. This is the first scan. Save the baseline.
                save_fim_baseline(filepath, current_hash)
                # Add an INFO finding just to note that a baseline was established.
                findings.append({
                    "id": "FIM-INFO",
                    "category": "FIM",
                    "severity": "INFO",
                    "title": "Baseline Established",
                    "description": f"Initial SHA-256 baseline recorded for {filepath}."
                })
            else:
                if current_hash != baseline_hash:
                    findings.append({
                        "id": "FIM-001",
                        "category": "FIM",
                        "severity": "CRITICAL",
                        "title": "File Integrity Violation",
                        "description": f"The hash for {filepath} has changed! Baseline: {baseline_hash[:8]}... Current: {current_hash[:8]}... This indicates tampering or rootkit activity."
                    })
        
    except Exception as e:
        findings.append({
            "id": "FIM-ERR",
            "category": "FIM",
            "severity": "MEDIUM",
            "title": "FIM Engine Failure",
            "description": str(e)
        })
        
    return findings
