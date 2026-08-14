# Phase 16: Automated Testing & Reliability

## 16.1 Academic Overview
In a commercial software environment, pushing broken code to production is catastrophic. Phase 16 introduces Test-Driven Development (TDD) concepts to mathematically prove the reliability of the Risk Scoring Engine.

## 16.2 Technical Implementation
The platform uses the built-in `unittest` framework to isolate the `modules/score.py` algorithm from the rest of the application.

Rather than waiting 10 seconds for a real system scan to run, the test suite injects mocked (fake) JSON vulnerability payloads directly into the `calculate_score()` function.
- `test_calculate_score_perfect()`: Injects an empty array and asserts the engine returns `135/135`.
- `test_calculate_score_floor()`: Injects three `CRITICAL` service vulnerabilities (3 * -10 = -30 points) into a category with a maximum weight of 10 points. It asserts via `self.assertEqual()` that the category score properly stops at `0` and does not bleed negative points into the total score.
