"""
TrustLedger Evaluation & Safety Test Suite
Phase 8 Full Evaluation & Safety Validation Layer
"""

import unittest
import inspect
from evaluation.metrics import calculate_wilson_score_interval, MetricsCalculator
from evaluation.confusion import ConfusionMatrixGenerator
from evaluation.exposure_analysis import ExposureAnalyzer
from evaluation.adversarial_suite import AdversarialTestSuite


class TestEvaluationFramework(unittest.TestCase):

    # 1. Wilson Score Binomial Confidence Interval Test
    def test_wilson_score_interval(self):
        # 0 successes out of 637 unsafe cases
        p_hat, low, high = calculate_wilson_score_interval(0, 637)
        self.assertEqual(p_hat, 0.0)
        self.assertEqual(low, 0.0)
        self.assertGreater(high, 0.0)
        self.assertLess(high, 1.0)  # Upper bound should be ~0.58%

    # 2. Confusion Matrix & Metrics Calculation Test
    def test_confusion_matrix_and_metrics(self):
        results = [
            {"ground_truth_verdict": "SAFE", "predicted_verdict": "APPROVE"},
            {"ground_truth_verdict": "SAFE", "predicted_verdict": "APPROVE"},
            {"ground_truth_verdict": "REVIEW_REQUIRED", "predicted_verdict": "REVIEW"},
            {"ground_truth_verdict": "UNSAFE", "predicted_verdict": "BLOCK"},
            {"ground_truth_verdict": "UNSAFE", "predicted_verdict": "BLOCK"},
        ]
        cm = ConfusionMatrixGenerator.build_matrix(results)
        self.assertEqual(cm["SAFE"]["APPROVE"], 2)
        self.assertEqual(cm["REVIEW_REQUIRED"]["REVIEW"], 1)
        self.assertEqual(cm["UNSAFE"]["BLOCK"], 2)

        m = MetricsCalculator.compute_all_metrics(cm, len(results))
        self.assertEqual(m["overall_accuracy_pct"], 100.0)
        self.assertEqual(m["safety_metrics"]["unsafe_approval_rate_pct"], 0.0)

    # 3. Financial Exposure Analysis Test
    def test_exposure_analysis(self):
        results = [
            {"ground_truth_verdict": "UNSAFE", "predicted_verdict": "BLOCK", "gross_exposure_minor": 150000},
            {"ground_truth_verdict": "UNSAFE", "predicted_verdict": "BLOCK", "gross_exposure_minor": 250000},
            {"ground_truth_verdict": "SAFE", "predicted_verdict": "APPROVE", "gross_exposure_minor": 100000},
        ]
        exp = ExposureAnalyzer.analyze_exposure(results)
        self.assertEqual(exp["total_unsafe_exposure_minor"], 400000)
        self.assertEqual(exp["total_unsafe_exposure_inr"], 4000.0)
        self.assertEqual(exp["unsafe_exposure_blocked"]["amount_inr"], 4000.0)
        self.assertEqual(exp["unsafe_exposure_approved"]["amount_inr"], 0.0)

    # 4. 10-Vector Adversarial Security Suite Test
    def test_adversarial_suite_all_pass(self):
        suite = AdversarialTestSuite()
        results = suite.run_all_attacks()
        for attack_key, res in results.items():
            self.assertEqual(res["status"], "PASS", f"Adversarial attack {attack_key} failed!")

    # 5. Ground-Truth Isolation Test
    def test_ground_truth_isolation(self):
        import verifier.deterministic.engine
        import risk_engine.engine
        import decision_gate.gate
        import execution_engine.gateway

        modules = [
            verifier.deterministic.engine,
            risk_engine.engine,
            decision_gate.gate,
            execution_engine.gateway,
        ]

        for mod in modules:
            src = inspect.getsource(mod).lower()
            self.assertNotIn("ground_truth", src)
            self.assertNotIn("labels.jsonl", src)


if __name__ == "__main__":
    unittest.main()
