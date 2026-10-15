"""
 Project - MamaEarth Growth Intelligence Pipeline
Test Suite: test_narrator.py

Audits:
- Task 1: findings.json structure and non-empty values
- Task 2: SCR framework presence (Situation, Complication, Resolution)
- Task 3: Error handling returning structured dictionary
- Task 4: Offline fallback generation without API key or network
- Task 5: 5/5 Numeric accuracy confirmation
"""

import os
import json
import unittest
from generate_findings import compute_growth_intelligence_findings
from narrator import (
    generate_offline_scr_narrative,
    generate_scr_narrative_with_gemini,
    verify_numeric_accuracy
)


class TestInsightNarrator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.findings = compute_growth_intelligence_findings()

    def test_task_1_findings_structure(self):
        """Verifies findings.json contains all required reconciled metrics."""
        self.assertIn('cleaned_total_revenue_inr', self.findings)
        self.assertIn('raw_total_revenue_inr', self.findings)
        self.assertIn('duplicate_reconciliation_delta_inr', self.findings)
        self.assertIn('return_rate_by_payment', self.findings)
        self.assertIn('highest_risk_segment', self.findings)
        self.assertIn('true_peak_month', self.findings)
        self.assertIn('outlier_inflated_month', self.findings)

        # Check values are computed numbers, not zeros
        self.assertGreater(self.findings['cleaned_total_revenue_inr'], 0)
        self.assertEqual(self.findings['highest_risk_segment']['return_rate_pct'], 54.5)

    def test_task_2_and_4_offline_scr_narrative(self):
        """Verifies offline template generates valid SCR structure with all 3 pillars."""
        narrative = generate_offline_scr_narrative(self.findings)
        self.assertIn("Situation", narrative)
        self.assertIn("Complication", narrative)
        self.assertIn("Resolution", narrative)

    def test_task_3_error_handling_and_fallback(self):
        """Verifies function returns a dictionary even on invalid credentials."""
        # Force an invalid API key to trigger error handling
        res = generate_scr_narrative_with_gemini(self.findings, api_key="INVALID_TEST_KEY_123")
        self.assertIsInstance(res, dict)
        self.assertIn("status", res)
        self.assertIn("narrative", res)
        self.assertIn("source", res)
        self.assertIn("parameters", res)
        self.assertEqual(res["parameters"]["temperature"], 0.0)

    def test_task_5_numeric_accuracy(self):
        """Verifies all five critical figures appear and pass validation."""
        narrative = generate_offline_scr_narrative(self.findings)
        accuracy = verify_numeric_accuracy(narrative, self.findings)
        self.assertTrue(accuracy['all_passed'])
        self.assertEqual(accuracy['passed_count'], 5)
        self.assertEqual(accuracy['total_checks'], 5)


if __name__ == '__main__':
    unittest.main()
