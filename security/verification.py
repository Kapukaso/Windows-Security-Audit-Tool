"""
security/verification.py
Native Windows Authenticode Validation and Contextual Alert Triage Layer.
"""

import ctypes
import ctypes.wintypes as wintypes
import hashlib
import sqlite3
import logging
import os
from typing import Dict, Any

# ============================================================================
# CTYPES DATA STRUCTURES & WINDOWS API BINDINGS
# ============================================================================

wintrust = ctypes.windll.wintrust

WTD_UI_NONE = 2
WTD_REVOKE_NONE = 0
WTD_CHOICE_FILE = 1
WTD_STATEACTION_IGNORE = 0
ERROR_SUCCESS = 0

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8)
    ]

class WINTRUST_FILE_INFO(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pcwszFilePath", wintypes.LPCWSTR),
        ("hFile", wintypes.HANDLE),
        ("pgKnownSubject", ctypes.c_void_p)
    ]

class WINTRUST_DATA(ctypes.Structure):
    _fields_ = [
        ("cbStruct", wintypes.DWORD),
        ("pPolicyCallbackData", wintypes.LPVOID),
        ("pSIPClientData", wintypes.LPVOID),
        ("dwUIChoice", wintypes.DWORD),
        ("fdwRevocationChecks", wintypes.DWORD),
        ("dwUnionChoice", wintypes.DWORD),
        ("pFile", ctypes.POINTER(WINTRUST_FILE_INFO)),
        ("dwStateAction", wintypes.DWORD),
        ("hWVTStateData", wintypes.HANDLE),
        ("pwszURLReference", wintypes.LPCWSTR),
        ("dwProvFlags", wintypes.DWORD),
        ("dwUIContext", wintypes.DWORD),
        ("pSignatureSettings", wintypes.LPVOID)
    ]

ACTION_GENERIC_VERIFY_V2 = GUID(
    0x00AAC56B, 0xCD44, 0x11D0,
    (ctypes.c_ubyte * 8)(0x8C, 0xC2, 0x00, 0xC0, 0x4F, 0xC2, 0x95, 0xEE)
)

WinVerifyTrust = wintrust.WinVerifyTrust
WinVerifyTrust.argtypes = [wintypes.HWND, ctypes.POINTER(GUID), ctypes.POINTER(WINTRUST_DATA)]
WinVerifyTrust.restype = wintypes.LONG

# ============================================================================
# LIGHTWEIGHT SQLITE CACHE LAYER
# ============================================================================

class SignatureCache:
    def __init__(self, db_path: str = ":memory:", max_size: int = 5000):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.max_size = max_size
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_signatures (
                sha256_hash TEXT PRIMARY KEY,
                is_signed BOOLEAN,
                file_path TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_seen ON file_signatures(last_seen)')
        self.conn.commit()

    def get_signature_status(self, file_hash: str):
        self.cursor.execute("SELECT is_signed FROM file_signatures WHERE sha256_hash = ?", (file_hash,))
        row = self.cursor.fetchone()
        if row:
            # Update last_seen for LRU
            self.cursor.execute("UPDATE file_signatures SET last_seen = CURRENT_TIMESTAMP WHERE sha256_hash = ?", (file_hash,))
            self.conn.commit()
            return bool(row[0])
        return None

    def set_signature_status(self, file_hash: str, is_signed: bool, file_path: str) -> None:
        self.cursor.execute('''
            INSERT OR REPLACE INTO file_signatures (sha256_hash, is_signed, file_path, last_seen)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (file_hash, is_signed, file_path))
        
        # Enforce LRU Cache Size
        self.cursor.execute('SELECT COUNT(*) FROM file_signatures')
        count = self.cursor.fetchone()[0]
        if count > self.max_size:
            # Delete oldest entries
            self.cursor.execute('''
                DELETE FROM file_signatures 
                WHERE sha256_hash IN (
                    SELECT sha256_hash FROM file_signatures 
                    ORDER BY last_seen ASC 
                    LIMIT ?
                )
            ''', (count - self.max_size,))
            
        self.conn.commit()

# ============================================================================
# SMART VERIFICATION ENGINE
# ============================================================================

class SmartVerificationEngine:
    def __init__(self):
        self.cache = SignatureCache(max_size=5000)
        self.logger = logging.getLogger("VerificationEngine")
        self.logger.setLevel(logging.INFO)
        self._prewarm_cache()
        
    def _prewarm_cache(self):
        # Pre-warm with known Windows binary hashes to bypass wintrust entirely for common operations
        known_safe_hashes = {
            # Examples of pre-calculated hashes (simulated dummy hashes for demonstration)
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": "C:\\Windows\\System32\\svchost.exe",
            "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92": "C:\\Windows\\explorer.exe"
        }
        for file_hash, file_path in known_safe_hashes.items():
            self.cache.set_signature_status(file_hash, True, file_path)

    def _calculate_sha256(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (PermissionError, FileNotFoundError):
            return ""

    def verify_authenticode_signature(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False

        file_hash = self._calculate_sha256(file_path)
        if not file_hash:
            return False
            
        cached_status = self.cache.get_signature_status(file_hash)
        if cached_status is not None:
            return cached_status

        file_info = WINTRUST_FILE_INFO()
        file_info.cbStruct = ctypes.sizeof(WINTRUST_FILE_INFO)
        file_info.pcwszFilePath = file_path
        file_info.hFile = None
        file_info.pgKnownSubject = None

        wintrust_data = WINTRUST_DATA()
        wintrust_data.cbStruct = ctypes.sizeof(WINTRUST_DATA)
        wintrust_data.pPolicyCallbackData = None
        wintrust_data.pSIPClientData = None
        wintrust_data.dwUIChoice = WTD_UI_NONE
        wintrust_data.fdwRevocationChecks = WTD_REVOKE_NONE
        wintrust_data.dwUnionChoice = WTD_CHOICE_FILE
        wintrust_data.pFile = ctypes.pointer(file_info)
        wintrust_data.dwStateAction = WTD_STATEACTION_IGNORE
        wintrust_data.hWVTStateData = None
        wintrust_data.pwszURLReference = None
        wintrust_data.dwProvFlags = 0
        wintrust_data.dwUIContext = 0
        wintrust_data.pSignatureSettings = None

        status = WinVerifyTrust(None, ctypes.byref(ACTION_GENERIC_VERIFY_V2), ctypes.byref(wintrust_data))
        is_signed = (status == ERROR_SUCCESS)
        
        self.cache.set_signature_status(file_hash, is_signed, file_path)
        return is_signed

# Singleton instance to persist cache across module calls
VERIFICATION_ENGINE = SmartVerificationEngine()
