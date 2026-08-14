# Phase 11: Risk Scoring Engine

## 11.1 Academic Overview & Motivation
To make security telemetry actionable for non-technical stakeholders, it must be quantified. Phase 11 acts as the mathematical core of the Defiant Platform, translating hundreds of boolean data points into a standardized, CVSS-inspired Risk Score.

## 11.2 Algorithm & Mathematics
The engine operates on a Base-Weight and Severity-Deduction model.

1. **Category Weights (Total 135 Points):**
   Categories are weighted by their systemic importance. 
   `{Defender: 20, Firewall: 20, Users: 15, Passwords: 15, Updates: 15, Network: 10, Services: 10, Startup: 10, Software: 10, Logs: 10}`

2. **Severity Deductions:**
   Iterates through the `all_findings` array and applies subtraction logic.
   `CRITICAL = -10`, `HIGH = -5`, `MEDIUM = -2`, `LOW = -1`.

3. **Floor Function (Zero-Bounding):**
   ```python
   category_scores[category] -= deduction
   if category_scores[category] < 0:
       category_scores[category] = 0
   ```
   *Justification:* If a system has 10 critical service vulnerabilities, the Service category loses 100 points. Without the floor function, this would result in a negative total score, breaking the UI gauge. Zero-bounding ensures a category maxes out its penalty.
