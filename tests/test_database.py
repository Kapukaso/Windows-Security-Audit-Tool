"""
tests/test_database.py
Comprehensive unit tests for database/database.py.
Validates schema parity, scan CRUD, FIM baselines, CVE caching, telemetry, and fallback.
"""
import sqlite3
import json
from datetime import datetime, timedelta
import pytest

from database.database import (
    init_db,
    is_postgres,
    get_connection,
    save_scan_results,
    get_scan_history,
    save_fim_baseline,
    get_fim_baseline,
    reset_fim_baselines,
    save_cve_cache,
    get_cve_cache,
    save_telemetry,
    get_telemetry_baseline,
    maintain_database
)


def test_init_db_creates_all_tables(in_memory_db):
    """Verifies all core tables are initialized with proper SQLite schema."""
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    expected_tables = {
        "scans",
        "findings",
        "fim_baselines",
        "telemetry_log",
        "nvd_cve_cache"
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

    # Verify idempotency by calling init_db again
    init_db()


def test_is_postgres_detection(in_memory_db):
    """Verifies is_postgres correctly returns False for standard SQLite connections."""
    assert is_postgres(in_memory_db) is False


def test_save_and_get_scan_results(in_memory_db):
    """Tests storing and retrieving full audit scan results with nested findings."""
    sys_info = {
        "Hostname": "TEST-HOST",
        "Operating System": "Windows",
        "OS Version": "11.0",
        "Current User": "Auditor"
    }
    score_data = {
        "total_earned": 95,
        "total_possible": 100,
        "percentage": 95.0,
        "category_scores": {"Defender": 10, "Firewall": 10}
    }
    findings = [
        {
            "id": "DEF-001",
            "title": "Defender Disabled",
            "category": "Defender",
            "severity": "HIGH",
            "description": "Real-time monitoring is disabled.",
            "recommendation": "Enable real-time protection."
        },
        {
            "id": "NET-002",
            "title": "SMBv1 Exposed",
            "category": "Network",
            "severity": "HIGH",
            "description": "SMBv1 is active.",
            "recommendation": "Disable SMBv1."
        }
    ]

    scan_id = save_scan_results(sys_info, score_data, findings)
    assert scan_id is not None
    assert scan_id > 0

    history = get_scan_history()
    assert len(history) >= 1
    latest_scan = history[0]

    assert latest_scan["id"] == scan_id
    assert latest_scan["total_earned"] == 95
    assert latest_scan["percentage"] == 95.0
    assert latest_scan["hostname"] == "TEST-HOST"


def test_fim_baseline_crud_and_reset(in_memory_db):
    """Tests saving, querying, and resetting File Integrity Monitoring (FIM) baselines."""
    test_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
    test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Query before saving -> None
    assert get_fim_baseline(test_path) is None

    # Save baseline
    save_fim_baseline(test_path, test_hash)
    record = get_fim_baseline(test_path)
    assert record is not None
    assert record == test_hash

    # Save update to baseline
    new_hash = "01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b"
    save_fim_baseline(test_path, new_hash)
    updated_record = get_fim_baseline(test_path)
    assert updated_record == new_hash

    # Reset baselines
    deleted_count = reset_fim_baselines()
    assert deleted_count >= 1
    assert get_fim_baseline(test_path) is None


def test_cve_cache_hit_miss_and_ttl(in_memory_db):
    """Tests CVE caching: cache miss, cache hit, and TTL expiration."""
    # 1. Cache Miss
    miss = get_cve_cache("DefiantSecurityApp", "1.0.0")
    assert miss is None

    # 2. Save & Hit
    sample_cves = [
        {
            "cve_id": "CVE-2026-9999",
            "cvss": 8.5,
            "description": "Mock remote code execution vulnerability."
        }
    ]
    save_cve_cache("DefiantSecurityApp", "1.0.0", sample_cves)

    hit = get_cve_cache("DefiantSecurityApp", "1.0.0")
    assert hit is not None
    assert len(hit) == 1
    assert hit[0]["cve_id"] == "CVE-2026-9999"

    # 3. TTL Expiration: Simulate entry from 10 days ago
    cursor = in_memory_db.cursor()
    expired_timestamp = (datetime.now() - timedelta(days=10)).isoformat()
    cursor.execute("""
        INSERT INTO nvd_cve_cache (software_name, software_version, cve_data, timestamp)
        VALUES (?, ?, ?, ?)
    """, ("OldVulnerableApp", "0.9.0", json.dumps(sample_cves), expired_timestamp))
    in_memory_db.commit()

    # Query with default 7-day TTL -> should be treated as expired (None)
    expired_result = get_cve_cache("OldVulnerableApp", "0.9.0", max_age_days=7)
    assert expired_result is None

    # Query with 14-day TTL -> should find it
    non_expired_result = get_cve_cache("OldVulnerableApp", "0.9.0", max_age_days=14)
    assert non_expired_result is not None


def test_telemetry_saving_and_baseline(in_memory_db):
    """Tests recording system telemetry metrics and retrieving baseline array."""
    save_telemetry(15.5, 45.0)
    save_telemetry(20.0, 50.0)
    save_telemetry(35.2, 60.5)

    baseline = get_telemetry_baseline(limit=10)
    assert len(baseline) == 3
    # Ordered by id DESC (latest first)
    assert baseline[0] == (35.2, 60.5)
    assert baseline[1] == (20.0, 50.0)
    assert baseline[2] == (15.5, 45.0)


def test_maintain_database_pruning(in_memory_db):
    """Tests database maintenance cleanup without errors."""
    save_telemetry(10.0, 40.0)
    maintain_database(retention_days=7, max_scans=10)


def test_postgres_fallback_to_sqlite(monkeypatch, tmp_path):
    """
    Tests that get_connection() gracefully falls back to SQLite
    when DB_ENGINE is set to 'postgres' but PostgreSQL connection fails.
    """
    import database.database as target_db
    monkeypatch.setattr(target_db, "DB_ENGINE", "postgres")

    class MockPsycopg2:
        extensions = None
        @staticmethod
        def connect(url):
            raise ConnectionError("PostgreSQL server unreachable on port 5432")

    monkeypatch.setattr(target_db, "psycopg2", MockPsycopg2)
    temp_sqlite_file = str(tmp_path / "fallback.db")
    monkeypatch.setattr(target_db, "SQLITE_PATH", temp_sqlite_file)

    conn = target_db.get_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()


def test_sanitize_null_bytes_prevents_nul_errors(in_memory_db):
    """
    Verifies that sanitize_null_bytes strips NUL (0x00) characters from strings,
    lists, and dicts, and ensures data with embedded NUL characters can be stored
    cleanly in database functions without raising 'A string literal cannot contain NUL'.
    """
    from database.database import sanitize_null_bytes

    # 1. Test basic string sanitization
    raw_str = "Google\x00 Chrome\x00"
    cleaned = sanitize_null_bytes(raw_str)
    assert cleaned == "Google Chrome"
    assert "\x00" not in cleaned

    # 2. Test nested dict & list sanitization
    nested_data = {
        "title\x00": "Vulnerability\x00 Detected",
        "tags": ["critical\x00", {"id\x00": "DEF-\x00001"}]
    }
    clean_nested = sanitize_null_bytes(nested_data)
    assert "title" in clean_nested
    assert clean_nested["title"] == "Vulnerability Detected"
    assert clean_nested["tags"][0] == "critical"
    assert clean_nested["tags"][1]["id"] == "DEF-001"

    # 3. Test saving scan results containing embedded NUL characters
    sys_info = {"Hostname": "TEST-HOST\x00-CORRUPTED"}
    score_data = {"total_earned": 90, "total_possible": 100, "percentage": 90.0}
    findings = [{
        "id": "CORRUPT\x00-001",
        "category": "Registry\x00",
        "severity": "HIGH\x00",
        "title": "Corrupt registry string with nulls\x00 here"
    }]
    scan_id = save_scan_results(sys_info, score_data, findings)
    assert scan_id is not None

    # Verify stored data does not contain \x00
    cursor = in_memory_db.cursor()
    cursor.execute("SELECT hostname FROM scans WHERE id = ?", (scan_id,))
    stored_host = cursor.fetchone()[0]
    assert "\x00" not in stored_host
    assert stored_host == "TEST-HOST-CORRUPTED"

    cursor.execute("SELECT finding_id, category, severity, title FROM findings WHERE scan_id = ?", (scan_id,))
    stored_finding = cursor.fetchone()
    for field in stored_finding:
        assert "\x00" not in str(field)
    cursor.close()
    in_memory_db.commit()

    # 4. Test saving CVE cache with NUL bytes
    save_cve_cache("App\x00WithNull", "1.0\x00", [{"desc": "CVE\x00 description"}])
    cached = get_cve_cache("AppWithNull", "1.0")
    assert cached is not None

    # 5. Test saving FIM baseline with NUL bytes
    save_fim_baseline("C:\\test\\file\x00.exe", "hash\x00123")
    retrieved = get_fim_baseline("C:\\test\\file.exe")
    assert retrieved == "hash123"

