---
last_mapped_commit: f61906e15b5f40f34417ffe3a12a6a7015696188
last_mapped_at: 2026-10-17
---
# Testing Patterns

**Analysis Date:** 2026-10-17

## Test Framework

**Runner:**
- Standard Python `unittest` framework
- Config: Built-in discovery (`tests/` directory)

**Assertion Library:**
- Standard library `unittest.TestCase` assertions (`self.assertEqual`)

**Run Commands:**

```bash

# Run all platform unit tests

python -m unittest tests/test_audit.py

# Run with verbose output

python -m unittest -v tests/test_audit.py

# Run discovery across entire tests directory

python -m unittest discover -s tests -p "test_*.py"
```

## Test File Organization

**Location:**
- Centralized in `tests/` directory at repository root

**Naming:**
- Files: `test_<module_name>.py` (e.g. `tests/test_audit.py`)
- Classes: `Test<FeatureName>(unittest.TestCase)` (e.g. `TestSecurityPlatform`)
- Methods: `test_<behavior_being_verified>` (e.g. `test_calculate_score_floor`)

**Structure:**

```
tests/
└── test_audit.py        # Unit tests for scoring engine, category weights, and floor bounds
```

## Test Structure

**Suite Organization:**

```python
import unittest
from modules.score import calculate_score

class TestSecurityPlatform(unittest.TestCase):

    def test_calculate_score_perfect(self):
        """
        Tests that an empty finding list returns a perfect 190/190 score.
        """
        old_scores = {
            "Defender": 10,
            "Firewall": 10,
            "Users": 10
        }
        all_findings = []  # No negative findings
        
        score_data = calculate_score(all_findings, old_scores)
        
        self.assertEqual(score_data['total_earned'], 190)
        self.assertEqual(score_data['total_possible'], 190)
```

**Patterns:**
- **Deterministic Pure Function Testing:** `calculate_score` takes pure input structures (`all_findings: list`, `old_module_scores: dict`) and returns deterministic scoring dicts, making tests fast and reproducible.
- **Boundary Verification:** Tests explicitly check mathematical invariants, such as ensuring a category with 3 critical deductions (30 points) floors at 0 rather than negative values (`test_calculate_score_floor`).

## Mocking

**Framework:**
- Python standard `unittest.mock` (available, but current tests rely primarily on synthesized in-memory finding objects)

**What to Mock:**
- PowerShell command outputs from `utils/powershell.py:run_powershell` and `run_powershell_json`
- NIST NVD HTTP responses from `urllib.request.urlopen` in `modules/cve_lookup.py`
- CrowdStrike Falcon API HTTP authentication and IOC responses in `modules/threat_intel.py`
- Native Win32 API calls (`ctypes.windll.wintrust`) in `security/verification.py`
- Database connections (`database.database.get_connection`) when testing DB CRUD operations

**What NOT to Mock:**
- Scoring calculation logic (`modules/score.py`)
- Compliance cross-reference mapping logic (`modules/compliance.py`)
- In-memory data transformations and report formatting (`modules/report.py`)

## Fixtures and Factories

**Test Data:**
- Synthetic finding dictionaries constructed inline inside test methods:

```python
sample_finding = {
    "id": "UPD-003",
    "category": "Updates",
    "severity": "HIGH",
    "title": "Outdated Security Patches"
}
```

**Location:**
- Constructed within test test methods in `tests/test_audit.py`.

## Coverage

**Requirements:**
- No automated minimum coverage thresholds currently enforced in CI.

**View Coverage:**

```bash

# If coverage.py is installed in the virtual environment:

pip install coverage
coverage run -m unittest discover -s tests
coverage report -m
coverage html
```

## Test Types

**Unit Tests:**
- Scope: Scoring math, category weight scaling, severity penalties, and floor limits in `tests/test_audit.py`.

**Integration Tests:**
- Current State: Manual execution of `python main.py` or running audits via web dashboard (`http://localhost:5000`).
- Gaps: Automated integration tests verifying actual Windows WMI queries, Registry queries, and Defender state inspection are not yet automated.

**E2E Tests:**
- Scope: Not automated. Frontend HUD interaction and remediation rollback verified manually.

## Common Patterns

**Error & Edge Case Testing:**

```python
def test_calculate_score_floor(self):
    """Ensure category deductions never produce negative points."""
    findings = [
        {"category": "Services", "severity": "CRITICAL"},
        {"category": "Services", "severity": "CRITICAL"},
        {"category": "Services", "severity": "CRITICAL"}
    ]
    score_data = calculate_score(findings, {})
    self.assertEqual(score_data['category_scores']['Services'], 0)
    self.assertGreaterEqual(score_data['total_earned'], 0)
```

---

*Testing analysis: 2026-10-17*
