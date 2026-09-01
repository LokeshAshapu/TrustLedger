"""
TrustLedger Deterministic Trust Engine Unit Test Suite
Phase 3 Deterministic Verification Layer
"""

import json
import os
import unittest
from datetime import datetime, timezone

from verifier.deterministic.engine import DeterministicTrustEngine
from verifier.deterministic.models import CheckStatus, FindingSeverity


class TestDeterministicTrustEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DeterministicTrustEngine()
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
                },
                "ev_failed": {
                    "contract_version": "trustledger.contract.v1",
                    "evidence_id": "ev_failed",
                    "evidence_type": "DELIVERY",
                    "source": "Courier",
                    "source_record_id": "ord_100",
                    "timestamp": self.base_time,
                    "verification_status": "FAILED",
                },
            },
            "transactions_db": {
                "txn_100": {
                    "transaction_id": "txn_100",
                    "order_id": "ord_100",
                    "merchant_id": "merch_001",
                    "customer_id": "cust_100",
                    "amount": {"amount_minor": 150000, "currency": "INR"},
                    "payment_method": "CARD",
                    "status": "CAPTURED",
                    "created_at": "2026-08-29T10:00:00Z",
                    "settled_at": "2026-08-29T10:05:00Z",
                },
                "txn_failed": {
                    "transaction_id": "txn_failed",
                    "order_id": "ord_200",
                    "merchant_id": "merch_001",
                    "customer_id": "cust_100",
                    "amount": {"amount_minor": 100000, "currency": "INR"},
                    "payment_method": "UPI",
                    "status": "FAILED",
                    "created_at": "2026-08-29T10:00:00Z",
                },
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
                "cust_100": {"customer_id": "cust_100", "merchant_id": "merch_001"},
                "cust_200": {"customer_id": "cust_200", "merchant_id": "merch_001"},
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
                        {"rule_id": "rule_refund_window", "rule_name": "Window", "threshold_value": 30, "is_hard_constraint": True},
                        {"rule_id": "rule_max_discount_pct", "rule_name": "Max Disc Pct", "threshold_value": 15.0, "is_hard_constraint": True},
                        {"rule_id": "rule_payout_auto_cap", "rule_name": "Payout Cap", "threshold_value": 10000000, "is_hard_constraint": True},
                        {"rule_id": "rule_max_recovery_retries", "rule_name": "Max Retries", "threshold_value": 3, "is_hard_constraint": True},
                    ],
                }
            },
            "refund_history_db": [],
        }

    # 1. Schema Validation Tests
    def test_schema_validator_valid(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_01",
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
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.schema_result.status, CheckStatus.PASS)

    def test_schema_validator_malformed(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_02",
            "action_type": "INVALID_ACTION",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "amount": {"amount_minor": -500, "currency": "INR"},
            "reason": {"category": "OTHER"},
            "evidence_references": [],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.schema_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "MALFORMED_DECISION_REQUEST" for f in res.hard_failures))

    # 2. Evidence Engine Tests
    def test_evidence_missing_reference(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_03",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "NON_DELIVERY"},
            "evidence_references": ["ev_nonexistent_99"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.evidence_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "MISSING_EVIDENCE_REFERENCE" for f in res.hard_failures))

    def test_evidence_status_failed(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_04",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "NON_DELIVERY"},
            "evidence_references": ["ev_failed"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.evidence_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "EVIDENCE_STATUS_FAILED" for f in res.hard_failures))

    # 3. Policy Engine Tests
    def test_policy_refund_cap_exceeded(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_05",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 6000000, "currency": "INR"},  # ₹60,000 > ₹25,000 cap
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.policy_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "REFUND_LIMIT_EXCEEDED" for f in res.hard_failures))

    def test_policy_discount_max_percentage_exceeded(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_06",
            "action_type": "DISCOUNT",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "order_id": "ord_100",
            "amount": {"amount_minor": 30000, "currency": "INR"},
            "discount_spec": {"type": "PERCENTAGE", "percentage_points": 25.0},  # 25% > 15% cap
            "reason": {"category": "PROMOTIONAL_DISCOUNT"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.policy_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "MAX_DISCOUNT_PERCENTAGE_EXCEEDED" for f in res.hard_failures))

    # 4. Consistency Engine Tests
    def test_consistency_customer_mismatch(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_07",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_200",  # Mismatched customer!
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.consistency_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "CUSTOMER_MISMATCH" for f in res.hard_failures))

    def test_consistency_nonexistent_transaction(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_08",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_nonexistent_999",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.consistency_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "REFERENCED_TRANSACTION_NOT_FOUND" for f in res.hard_failures))

    def test_consistency_state_contradiction_failed_txn(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_test_09",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_failed",
            "amount": {"amount_minor": 100000, "currency": "INR"},
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        res = self.engine.verify(req, self.context)
        self.assertEqual(res.consistency_result.status, CheckStatus.FAIL)
        self.assertTrue(any(f.code == "STATE_CONTRADICTION" for f in res.hard_failures))

    # 5. Held-Out Test Set Execution Verification
    def test_held_out_test_set_processing(self):
        test_split_path = "data/splits/test.jsonl"
        if not os.path.exists(test_split_path):
            self.skipTest("data/splits/test.jsonl not found")

        with open(test_split_path, "r", encoding="utf-8") as f:
            lines = [f.readline() for _ in range(10)]

        for line in lines:
            if not line.strip():
                continue
            req = json.loads(line)
            res = self.engine.verify(req, self.context)
            self.assertEqual(res.engine_version, "trustledger.deterministic.v1")
            self.assertIsNotNone(res.potential_exposure)


if __name__ == "__main__":
    unittest.main()
