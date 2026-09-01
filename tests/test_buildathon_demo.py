"""
TrustLedger Buildathon E2E Demo Harness Test Suite
Phase 11C.1 Buildathon E2E Demo Harness
"""

import unittest
from decision_gate.models import FinalVerdict
from execution_engine.models import AuthorizationStatus
from backend.repository import SyntheticDataRepository
from backend.orchestrator import TrustLedgerDecisionService
from evaluation.buildathon_demo import get_demo_context, make_demo_request, run_buildathon_demo


class TestBuildathonDemoHarness(unittest.TestCase):
    """
    Validates all 10 mandatory safety invariants of the Buildathon E2E Demo Harness.
    """

    def setUp(self):
        self.repository = SyntheticDataRepository()
        self.service = TrustLedgerDecisionService(data_repository=self.repository)

    # 1. Safe scenario returns APPROVE
    def test_1_safe_scenario_returns_approve(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t1", 150000, ["ev_001"], "Safe refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertEqual(decision.verdict, FinalVerdict.APPROVE)
        self.assertEqual(decision.decision_rule, "TL-DG-010")

    # 2. Safe scenario produces authorization (ISSUED)
    def test_2_safe_scenario_produces_authorization(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t2", 150000, ["ev_001"], "Safe refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertIsNotNone(auth)
        self.assertEqual(auth.status, AuthorizationStatus.ISSUED)

    # 3. Review scenario returns REVIEW
    def test_3_review_scenario_returns_review(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t3", 50000, ["ev_stale_999"], "Stale evidence refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertEqual(decision.verdict, FinalVerdict.REVIEW)
        self.assertEqual(decision.decision_rule, "TL-DG-003")

    # 4. Review has no authorization (None)
    def test_4_review_scenario_has_no_authorization(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t4", 50000, ["ev_stale_999"], "Stale evidence refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertIsNone(auth)

    # 5. Block scenario returns BLOCK
    def test_5_block_scenario_returns_block(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t5", 6000000, ["ev_001"], "Over cap refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertEqual(decision.verdict, FinalVerdict.BLOCK)
        self.assertEqual(decision.decision_rule, "TL-DG-002")

    # 6. Block has no authorization (None)
    def test_6_block_scenario_has_no_authorization(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t6", 6000000, ["ev_001"], "Over cap refund", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertIsNone(auth)

    # 7. BLOCK produces zero Razorpay calls
    def test_7_block_produces_zero_razorpay_calls(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t7", 6000000, ["ev_001"], "Over cap refund", ctx)
        decision, auth = self.service.verify_decision(req)

        exec_res = self.service.execute_decision("dec_t7", "auth_fake", "pay_t7")

        self.assertNotEqual(exec_res.provider, "razorpay")
        self.assertIn(exec_res.status.value, ["DENIED", "REJECTED"])

    # 8. REVIEW produces zero Razorpay calls
    def test_8_review_produces_zero_razorpay_calls(self):
        ctx = get_demo_context(policy_cap_minor=2500000)
        req = make_demo_request("dec_t8", 50000, ["ev_stale_999"], "Stale evidence refund", ctx)
        decision, auth = self.service.verify_decision(req)

        exec_res = self.service.execute_decision("dec_t8", "auth_fake", "pay_t8")

        self.assertNotEqual(exec_res.provider, "razorpay")
        self.assertIn(exec_res.status.value, ["DENIED", "REJECTED"])

    # 9. AI SUPPORT cannot override policy-cap violation
    def test_9_ai_support_cannot_override_policy_cap(self):
        ctx = get_demo_context(policy_cap_minor=2500000) # ₹25,000 policy cap
        req = make_demo_request("dec_t9", 6000000, ["ev_001"], "High value refund request", ctx)
        decision, auth = self.service.verify_decision(req)

        self.assertEqual(decision.verdict, FinalVerdict.BLOCK)
        self.assertEqual(decision.decision_rule, "TL-DG-002")
        self.assertTrue(any("REFUND_LIMIT_EXCEEDED" in f or "POLICY_CAP" in f for f in decision.contributing_findings))
        self.assertIsNone(auth)

    # 10. Full demo returns success
    def test_10_full_demo_returns_success(self):
        exit_code = run_buildathon_demo(verbose=False)
        self.assertEqual(exit_code, 0)
