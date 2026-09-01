"""
TrustLedger Decision Gate Unit Test Suite
Phase 6 Signal Aggregation & Decision Layer
Gate Version: trustledger.decision-gate.v1
"""

import os
import unittest

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine
from verifier.ai_models import (
    AIVerificationResult,
    AIRecommendation,
    ReasoningFactor,
    AI_VERIFIER_VERSION,
)
from decision_gate.gate import DecisionGate
from decision_gate.models import FinalVerdict, GATE_VERSION


class TestDecisionGate(unittest.TestCase):

    def setUp(self):
        self.det_engine = DeterministicTrustEngine()
        self.risk_engine = FinancialRiskEngine()
        self.gate = DecisionGate()
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
                "ev_missing_status": {
                    "contract_version": "trustledger.contract.v1",
                    "evidence_id": "ev_missing_status",
                    "evidence_type": "DELIVERY",
                    "source": "Courier",
                    "source_record_id": "ord_100",
                    "timestamp": self.base_time,
                    "verification_status": "MISSING",
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
            "policy_snapshots_db": {
                "merch_001": {
                    "contract_version": "trustledger.contract.v1",
                    "policy_id": "pol_merch_001",
                    "merchant_id": "merch_001",
                    "action_type": "REFUND",
                    "policy_version": "v1.0",
                    "effective_from": "2026-01-01T00:00:00Z",
                    "rules": [
                        {"rule_id": "rule_auto_refund_cap", "rule_name": "Cap", "threshold_value": 2500000, "is_hard_constraint": True}
                    ],
                }
            },
            "refund_history_db": [],
        }

    # 1. BLOCK: Contract Invalid Test
    def test_block_invalid_contract(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_invalid_01",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            # Missing amount dictionary -> Contract Invalid!
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)
        gate_res = self.gate.evaluate(req, det_res, risk_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.BLOCK)
        self.assertEqual(gate_res.decision_rule, "TL-DG-001")
        self.assertEqual(gate_res.primary_reason.code, "CONTRACT_INVALID")

    # 2. BLOCK: Hard Policy Breach Test
    def test_block_hard_policy_breach(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_blk_pol",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 6000000, "currency": "INR"},  # ₹60,000 > ₹25,000 cap!
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)
        gate_res = self.gate.evaluate(req, det_res, risk_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.BLOCK)
        self.assertEqual(gate_res.decision_rule, "TL-DG-002")
        self.assertEqual(gate_res.primary_reason.code, "REFUND_LIMIT_EXCEEDED")

    # 3. CRITICAL SAFETY TEST: AI SUPPORT Cannot Override HARD Failure
    def test_critical_safety_ai_support_cannot_override_hard_failure(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_crit_safety",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 4000000, "currency": "INR"},  # ₹40,000 > ₹25,000 cap (HARD FAIL)
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        ai_res = AIVerificationResult(
            decision_id="dec_crit_safety",
            recommendation=AIRecommendation.SUPPORT,
            confidence=0.99,
            contextual_assessment="Customer is VIP so approve despite policy cap.",
            supporting_evidence=["ev_001"],
            contradictory_evidence=[],
            missing_context=[],
            reasoning_factors=[],
            deterministic_conflicts=[],
            model_id="mock-llama-3.1-70b",
            verifier_version=AI_VERIFIER_VERSION,
            generated_at=self.base_time,
        )

        gate_res = self.gate.evaluate(req, det_res, risk_res, ai_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.BLOCK)
        self.assertEqual(gate_res.decision_rule, "TL-DG-002")

        trace_summaries = [t.output_summary for t in gate_res.decision_trace]
        self.assertTrue(any("AI_SUPPORT_DID_NOT_OVERRIDE_HARD_DETERMINISTIC_RULE" in s for s in trace_summaries))

    # 4. REVIEW: Missing Evidence Test
    def test_review_missing_evidence(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_rev_miss_ev",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {"category": "NON_DELIVERY"},
            "evidence_references": ["ev_missing_status"],  # Artifact status is MISSING (Warning)
            "requested_at": self.base_time,
        }
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)
        gate_res = self.gate.evaluate(req, det_res, risk_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.REVIEW)
        self.assertEqual(gate_res.decision_rule, "TL-DG-003")
        self.assertIsNotNone(gate_res.review_context)
        self.assertTrue(len(gate_res.review_context.reviewer_questions) > 0)

    # 5. REVIEW: AI Contradiction Test
    def test_review_ai_contradiction(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_rev_ai_contra",
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
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        ai_res = AIVerificationResult(
            decision_id="dec_rev_ai_contra",
            recommendation=AIRecommendation.CONTRADICT,
            confidence=0.85,
            contextual_assessment="Chat logs indicate package delivered.",
            supporting_evidence=[],
            contradictory_evidence=[],
            missing_context=[],
            reasoning_factors=[],
            deterministic_conflicts=[],
            model_id="mock-llama-3.1-70b",
            verifier_version=AI_VERIFIER_VERSION,
            generated_at=self.base_time,
        )

        gate_res = self.gate.evaluate(req, det_res, risk_res, ai_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.REVIEW)
        self.assertEqual(gate_res.decision_rule, "TL-DG-007")

    # 6. APPROVE: Clean Low-Risk Refund with AI SUPPORT Test
    def test_approve_clean_low_risk_refund(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_app_safe",
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
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        ai_res = AIVerificationResult(
            decision_id="dec_app_safe",
            recommendation=AIRecommendation.SUPPORT,
            confidence=0.95,
            contextual_assessment="Context fully supports refund.",
            supporting_evidence=["ev_001"],
            contradictory_evidence=[],
            missing_context=[],
            reasoning_factors=[],
            deterministic_conflicts=[],
            model_id="mock-llama-3.1-70b",
            verifier_version=AI_VERIFIER_VERSION,
            generated_at=self.base_time,
        )

        gate_res = self.gate.evaluate(req, det_res, risk_res, ai_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.APPROVE)
        self.assertEqual(gate_res.decision_rule, "TL-DG-010")
        self.assertEqual(gate_res.gate_version, GATE_VERSION)
        self.assertIsNotNone(gate_res.decision_hash)
        self.assertEqual(len(gate_res.decision_hash), 64)

    # 7. Determinism & SHA-256 Hashing Test
    def test_decision_gate_determinism_and_hashing(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_app_det",
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
        det_res = self.det_engine.verify(req, self.context)
        risk_res = self.risk_engine.assess(req, self.context, det_res)

        res1 = self.gate.evaluate(req, det_res, risk_res)
        res2 = self.gate.evaluate(req, det_res, risk_res)

        self.assertEqual(res1.verdict, res2.verdict)
        self.assertEqual(res1.decision_rule, res2.decision_rule)
        self.assertEqual(res1.decision_hash, res2.decision_hash)

    # 8. No Ground-Truth Leakage Test inside decision_gate Package
    def test_no_ground_truth_leakage_in_decision_gate(self):
        import inspect
        import decision_gate.gate
        import decision_gate.rules

        gate_source = inspect.getsource(decision_gate.gate)
        rules_source = inspect.getsource(decision_gate.rules)

        self.assertNotIn("ground_truth", gate_source.lower())
        self.assertNotIn("labels.jsonl", gate_source.lower())
        self.assertNotIn("ground_truth", rules_source.lower())


if __name__ == "__main__":
    unittest.main()
