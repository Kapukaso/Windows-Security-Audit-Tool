"""
modules/score.py
Calculates the final security score based on all aggregated findings.
"""
from tabulate import tabulate

# Maximum possible scores per category
CATEGORY_WEIGHTS = {
    "Defender": 20,
    "Firewall": 20,
    "Users": 15,
    "Password Policy": 15,
    "Updates": 15,
    "Network": 10,
    "Services": 10,
    "Startup": 10,
    "Software": 10,
    "Event Logs": 10
}

# Severity point deductions
SEVERITY_DEDUCTIONS = {
    "CRITICAL": 10,
    "HIGH": 5,
    "MEDIUM": 2,
    "LOW": 1,
    "INFO": 0
}

def calculate_score(all_findings, old_module_scores=None):
    """
    Calculates category scores and the overall security score.
    Returns a dictionary of category scores and the final total.
    """
    category_scores = {cat: max_score for cat, max_score in CATEGORY_WEIGHTS.items()}
    
    # Apply pre-calculated scores from older Phase 1-3 modules
    if old_module_scores:
        for cat, score in old_module_scores.items():
            if cat in category_scores:
                # Scale the old out-of-10 score to the new weight
                # e.g. If Defender is 8/10, and weight is 20, new score is 16
                scaled_score = int((score / 10.0) * CATEGORY_WEIGHTS[cat])
                category_scores[cat] = scaled_score

    # Deduct points for each finding from Phase 4+ modules
    for finding in all_findings:
        if not isinstance(finding, dict):
            continue # Skip legacy string findings if any sneaked in
            
        category = finding.get("category")
        severity = finding.get("severity", "INFO")
        
        deduction = SEVERITY_DEDUCTIONS.get(severity, 0)
        
        if category in category_scores and category not in (old_module_scores or {}):
            category_scores[category] -= deduction
            # Floor category score at 0
            if category_scores[category] < 0:
                category_scores[category] = 0
                
    # Calculate total
    total_earned = sum(category_scores.values())
    total_possible = sum(CATEGORY_WEIGHTS.values())
    
    return {
        "category_scores": category_scores,
        "total_earned": total_earned,
        "total_possible": total_possible
    }

def display_final_score(score_data):
    """
    Displays the final security score transparently.
    """
    print("\n" + "=" * 60)
    print("FINAL SYSTEM SECURITY SCORE")
    print("=" * 60)
    
    table = []
    for cat, weight in CATEGORY_WEIGHTS.items():
        earned = score_data["category_scores"].get(cat, 0)
        table.append([cat, f"{earned} / {weight}"])
        
    print(
        tabulate(
            table,
            headers=["Category", "Score"],
            tablefmt="grid"
        )
    )
    
    percentage = (score_data['total_earned'] / score_data['total_possible']) * 100
    print(f"\nOVERALL SECURITY SCORE: {score_data['total_earned']} / {score_data['total_possible']} ({percentage:.1f}%)")
    print("Risk Model: Project-defined security posture score based on severity deductions.\n")
