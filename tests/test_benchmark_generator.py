"""
TrustLedger Benchmark Generator Automated Unit Test Suite
Phase 2 Benchmark Dataset Pipeline
"""

import json
import os
import random
import unittest
from datetime import datetime, timezone

from data.generator.entities import SyntheticWorld
from data.generator.scenarios import ScenarioGenerator
from verifier.contracts import DecisionRequest, ActionType, VerdictType

FORBIDDEN_KEYS = {
    "ground_truth",
    "correct_verdict",
    "scenario_label",
    "is_safe",
    "is_fraud",
    "expected_verdict",
    "expected_action",
    "ground_truth_verdict",
    "expected_safe_action",
    "financial_exposure_minor",
    "scenario_class",
    "difficulty",
}


class TestBenchmarkGenerator(unittest.TestCase):

    def setUp(self):
        self.seed = 20260829
        self.rng = random.Random(self.seed)
        self.base_time = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)
        self.world = SyntheticWorld(self.rng, self.base_time, time_window_days=180)
        self.world.generate_world(num_merchants=5, num_customers=100)
        self.generator = ScenarioGenerator(self.world, self.rng)

    def test_01_reproducibility(self):
        """Same seed -> identical decision and ground-truth output"""
        rng1 = random.Random(12345)
        world1 = SyntheticWorld(rng1, self.base_time, 180)
        world1.generate_world(5, 50)
        gen1 = ScenarioGenerator(world1, rng1)
        req1, gt1 = gen1.generate_case_for_class("CLASS_A", "EASY")

        rng2 = random.Random(12345)
        world2 = SyntheticWorld(rng2, self.base_time, 180)
        world2.generate_world(5, 50)
        gen2 = ScenarioGenerator(world2, rng2)
        req2, gt2 = gen2.generate_case_for_class("CLASS_A", "EASY")

        self.assertEqual(req1, req2)
        self.assertEqual(gt1, gt2)

    def test_02_contract_compatibility(self):
        """Generated DecisionRequest payloads pass Phase 1 Pydantic contract validation"""
        for cls in ["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D", "CLASS_E", "CLASS_F", "CLASS_G", "CLASS_H", "CLASS_I", "CLASS_J"]:
            req, _ = self.generator.generate_case_for_class(cls, "MEDIUM")
            parsed = DecisionRequest.model_validate(req)
            self.assertEqual(parsed.contract_version, "trustledger.contract.v1")
            self.assertIn(parsed.action_type, [ActionType.REFUND, ActionType.DISCOUNT, ActionType.PAYMENT_RECOVERY, ActionType.PAYOUT])

    def test_03_ground_truth_separation_leakage(self):
        """Ground-truth-only fields never appear inside observable payloads"""
        for cls in ["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D", "CLASS_E", "CLASS_F", "CLASS_G", "CLASS_H", "CLASS_I", "CLASS_J"]:
            req, gt = self.generator.generate_case_for_class(cls, "HARD")
            # Verify observable request payload has zero forbidden keys
            req_json = json.dumps(req)
            for forbidden_key in FORBIDDEN_KEYS:
                self.assertNotIn(f'"{forbidden_key}"', req_json)

            # Verify ground truth has expected evaluation keys
            self.assertIn("ground_truth_verdict", gt)
            self.assertIn("expected_verdict", gt)
            self.assertIn("financial_exposure_minor", gt)

    def test_04_monetary_integrity(self):
        """Monetary values are non-negative minor integers with uppercase ISO currencies"""
        for _ in range(50):
            req, _ = self.generator.generate_case_for_class("CLASS_A", "EASY")
            amt = req["amount"]
            self.assertIsInstance(amt["amount_minor"], int)
            self.assertGreaterEqual(amt["amount_minor"], 0)
            self.assertEqual(amt["currency"], "INR")

    def test_05_scenario_correctness_all_classes(self):
        """Scenario classes A-J deterministically produce expected ground-truth labels"""
        expected_mappings = {
            "CLASS_A": ("SAFE", "APPROVE"),
            "CLASS_B": ("UNSAFE", "BLOCK"),
            "CLASS_C": ("UNSAFE", "BLOCK"),
            "CLASS_D": ("UNSAFE", "BLOCK"),
            "CLASS_E": ("UNSAFE", "BLOCK"),
            "CLASS_F": ("REVIEW_REQUIRED", "REVIEW"),
            "CLASS_G": ("REVIEW_REQUIRED", "REVIEW"),
            "CLASS_H": ("REVIEW_REQUIRED", "REVIEW"),
            "CLASS_I": ("UNSAFE", "BLOCK"),
            "CLASS_J": ("UNSAFE", "BLOCK"),
        }

        for cls, (expected_gt, expected_v) in expected_mappings.items():
            _, gt = self.generator.generate_case_for_class(cls, "MEDIUM")
            self.assertEqual(gt["scenario_class"], cls)
            self.assertEqual(gt["ground_truth_verdict"], expected_gt)
            self.assertEqual(gt["expected_verdict"], expected_v)

    def test_06_referential_integrity(self):
        """Merchants, customers, and orders maintain valid relationships"""
        self.assertGreater(len(self.world.merchants), 0)
        self.assertGreater(len(self.world.customers), 0)
        self.assertGreater(len(self.world.transactions), 0)

        for txn in self.world.transactions.values():
            self.assertIn(txn["merchant_id"], self.world.merchants)
            self.assertIn(txn["customer_id"], self.world.customers)


if __name__ == "__main__":
    unittest.main()
