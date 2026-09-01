"""
TrustLedger Financial Risk Engine Unit Test Suite
Phase 4 Deterministic Financial Risk Layer
Methodology Version: trustledger.risk.v1
"""

import json
import os
import unittest

from verifier.deterministic.engine import DeterministicTrustEngine
from verifier.deterministic.models import MoneyAmount
from risk_engine.engine import FinancialRiskEngine
from risk_engine.models import RiskLevel, RISK_METHODOLOGY_VERSION


class TestFinancialRiskEngine(unittest.TestCase):

    def setUp(self):
        self.det_engine = DeterministicTrustEngine()
        self.risk_engine = FinancialRiskEngine()
        self.base_time = "2026-08-29T12:00:00Z"

        self.context = {
            "evidence_db": {
                "ev_001": {
                    "contract_version": "trustledger.contract.v1",
                    "evidence_id": "ev_001",
                    "evidence_type": "TRANSACTION",
                    "source": "Stripe",
                    "source_record_id": "txn_100",
                    "timestamp": self.base_time,
                    "verification_status": "VERIFIED",
                }
            },
            "transactions_db": {
                "txn_100": {
                    "transaction_id": "txn_100",
                    "order_id": "ord_100",
                    "merchant_id": "merch_001",
                    "customer_id": "cust_100",
                    "amount": {"amount_minor": 150000, "currency": "INR"},  # ₹1,500
                    "payment_method": "CARD",
                    "status": "CAPTURED",
                    "created_at": "2026-08-29T10:00:00Z",
                    "settled_at": "2026-08-29T10:05:00Z",
                }
            },
            "orders_db": {
                "ord_100": {
                    "order_id": "ord_100",
                    "merchant_id": "merch_001",
                    "customer_id": "cust_100",
                    "amount": {"amount_minor": 150000, "currency": "INR"},
                    "status": "FULFILLED",
                    "created_at": "2026-08-29T10:00:00Z",
                }
            },
            "customers_db": {
                "cust_100": {"customer_id": "cust_100", "merchant_id": "merch_001"}
            },
            "merchants_db": {
                "merch_001": {"merchant_id": "merch_001", "merchant_name": "Test Merchant"}
            },
            "policy_snapshots_db": {
                "merch_001": {
                    "contract_version": "trustledger.contract.v1",
                    "policy_id": "pol_merch_001",
                    "merchant_id": "merch_001",
                    "action_type": "REFUND",
                    "policy_version": "v1.0",
                    "effective_from": "2026-01-01T00:00:00Z",
                    "rules": [
                        {"rule_id": "rule_auto_refund_cap", "rule_name": "Cap", "threshold_value": 2500000, "is_hard_constraint": True},
                        {"rule_id": "rule_payout_auto_cap", "rule_name": "Payout Cap", "threshold_value": 10000000, "is_hard_constraint": True},
                    ],
                }
            },
            "refund_history_db": [],
        }

    # 1. Low Exposure Safe Action Test
    def test_low_exposure_safe_refund(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_risk_01",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},  # ₹1,500
            "reason": {"category": "NON_DELIVERY"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        self.assertEqual(risk_res.methodology_version, RISK_METHODOLOGY_VERSION)
        self.assertEqual(risk_res.risk_level, RiskLevel.LOW)
        self.assertLess(risk_res.risk_score, 0.25)
        self.assertEqual(risk_res.exposure.gross_exposure.amount_minor, 150000)
        self.assertEqual(risk_res.exposure.incremental_exposure.amount_minor, 0)
        self.assertEqual(len(risk_res.hard_risk_flags), 0)

    # 2. Critical Exposure Payout Test
    def test_critical_exposure_payout(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_risk_02",
            "action_type": "PAYOUT",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "amount": {"amount_minor": 30000000, "currency": "INR"},  # ₹300,000 > ₹200k threshold
            "reason": {"category": "SETTLEMENT"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        self.assertIn(risk_res.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])
        self.assertGreaterEqual(risk_res.risk_score, 0.50)
        self.assertIn("HIGH_FINANCIAL_EXPOSURE", risk_res.hard_risk_flags)
        self.assertIn("IRREVERSIBLE_ACTION", risk_res.hard_risk_flags)

    # 3. Policy Breach & Entity Mismatch Flags Test
    def test_policy_breach_and_mismatch_flags(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_risk_03",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_WRONG",  # Entity Mismatch!
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 6000000, "currency": "INR"},  # ₹60,000 > ₹25,000 cap!
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        self.assertIn("POLICY_BREACH", risk_res.hard_risk_flags)
        self.assertIn("ENTITY_MISMATCH", risk_res.hard_risk_flags)
        self.assertIn("MULTIPLE_HARD_FINDINGS", risk_res.hard_risk_flags)
        self.assertGreaterEqual(risk_res.risk_score, 0.50)

    # 4. Determinism Test
    def test_risk_assessment_determinism(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_risk_det",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "NON_DELIVERY"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res1 = self.det_engine.verify(req, self.context)
        res1 = self.risk_engine.assess(req, self.context, det_res1)

        det_res2 = self.det_engine.verify(req, self.context)
        res2 = self.risk_engine.assess(req, self.context, det_res2)

        self.assertEqual(res1.risk_score, res2.risk_score)
        self.assertEqual(res1.risk_level, res2.risk_level)
        self.assertEqual(res1.hard_risk_flags, res2.hard_risk_flags)
        self.assertEqual(len(res1.factors), len(res2.factors))

    # 5. Held-Out Dataset Execution Test
    def test_held_out_test_split_processing(self):
        test_split_path = "data/splits/test.jsonl"
        if not os.path.exists(test_split_path):
            self.skipTest("data/splits/test.jsonl not found")

        with open(test_split_path, "r", encoding="utf-8") as f:
            lines = [f.readline() for _ in range(10)]

        for line in lines:
            if not line.strip():
                continue
            req = json.loads(line)
            det_res = self.det_engine.verify(req, self.context)
            risk_res = self.risk_engine.assess(req, self.context, det_res)

            self.assertEqual(risk_res.methodology_version, RISK_METHODOLOGY_VERSION)
            self.assertTrue(0.0 <= risk_res.risk_score <= 1.0)
            self.assertIn(risk_res.risk_level, [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])


if __name__ == "__main__":
    unittest.main()
