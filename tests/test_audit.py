"""
tests/test_audit.py
Automated Unit Tests for the Windows Security Platform.
"""
import unittest
from modules.score import calculate_score

class TestSecurityPlatform(unittest.TestCase):

    def test_calculate_score_perfect(self):
        """
        Tests that an empty finding list returns a perfect 100/100 score.
        """
        old_scores = {
            "Defender": 10,
            "Firewall": 10,
            "Users": 10
        }
        all_findings = [] # No negative findings
        
        score_data = calculate_score(all_findings, old_scores)
        
        self.assertEqual(score_data['total_earned'], 190)
        self.assertEqual(score_data['total_possible'], 190)

    def test_calculate_score_with_deductions(self):
        """
        Tests that severity deductions are correctly applied.
        """
        old_scores = {
            "Defender": 10,
            "Firewall": 10,
            "Users": 10
        }
        
        # Simulate a high severity finding in Updates (deducts 5 points from Updates category)
        all_findings = [
            {
                "id": "UPD-003",
                "category": "Updates",
                "severity": "HIGH",
                "title": "Outdated Security Patches"
            }
        ]
        
        score_data = calculate_score(all_findings, old_scores)
        
        # Max score is 190. Minus 5 for a HIGH severity finding.
        self.assertEqual(score_data['total_earned'], 185)
        # Updates category normally has a max of 15. It should now be 10.
        self.assertEqual(score_data['category_scores']['Updates'], 10)

    def test_calculate_score_floor(self):
        """
        Tests that a category score cannot drop below zero.
        """
        old_scores = {
            "Defender": 10,
            "Firewall": 10,
            "Users": 10
        }
        
        # Simulate 3 critical findings in Services (deducts 30 points total from Services category)
        all_findings = [
            {"category": "Services", "severity": "CRITICAL"},
            {"category": "Services", "severity": "CRITICAL"},
            {"category": "Services", "severity": "CRITICAL"}
        ]
        
        score_data = calculate_score(all_findings, old_scores)
        
        # Services category has a max weight of 10. 
        # Deducting 30 points should floor it at 0, not -20.
        self.assertEqual(score_data['category_scores']['Services'], 0)
        self.assertEqual(score_data['total_earned'], 180) # Only lost the 10 points from Services

if __name__ == '__main__':
    unittest.main()
