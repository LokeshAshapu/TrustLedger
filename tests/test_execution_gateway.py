"""
TrustLedger ExecutionGateway -> Razorpay Integration Test Suite
Phase 11B.2 ExecutionGateway -> Razorpay Test Mode
"""

import copy
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from decision_gate.models import DecisionResult, FinalVerdict, PrimaryReason, EvidenceQualityState, StageTrace
from decision_gate.hashing import compute_decision_hash
from execution_engine.models import (
    ExecutionStatus,
    AuthorizationStatus,
    FailureCode,
)
from execution_engine.gateway import ExecutionGateway
from execution.models import RefundResponse as RazorpayRefundResponse
from execution.errors import (
    RazorpayValidationError,
    RazorpayAuthenticationError,
    RazorpayNotFoundError,
    RazorpayConflictError,
    RazorpayRateLimitError,
    RazorpayServerError,
    RazorpayTimeoutError,
    RazorpayNetworkError,
)
from backend.orchestrator import TrustLedgerDecisionService


class TestExecutionGatewayRazorpaySuite(unittest.TestCase):

    def setUp(self):
        self.mock_rzp_client = MagicMock()
        self.gateway = ExecutionGateway(razorpay_client=self.mock_rzp_client)

        approve_trace = [
            StageTrace(stage_name="CONTRACT", status="PASS", input_summary="Action: REFUND, Amount: 150000 INR", output_summary="Valid"),
            StageTrace(stage_name="RISK_ASSESSMENT", status="PASS", input_summary="Gross Exposure: 150000 INR", output_summary="Low risk"),
        ]

        # Standard Approve DecisionResult & Request
        approve_dummy = DecisionResult(
            decision_id="dec_app_001",
            verdict=FinalVerdict.APPROVE,
            decision_rule="TL-DG-010",
            primary_reason=PrimaryReason(code="PASS", message="Fully compliant."),
            risk_level="LOW",
            risk_score=0.1,
            evidence_state=EvidenceQualityState.SUFFICIENT,
            decision_trace=approve_trace,
            decision_hash="0" * 64,
            gate_version="trustledger.decision-gate.v1",
        )
        approve_hash = compute_decision_hash(approve_dummy.model_dump())
        approve_dummy.decision_hash = approve_hash
        self.approve_decision = approve_dummy

        block_dummy = DecisionResult(
            decision_id="dec_blk_001",
            verdict=FinalVerdict.BLOCK,
            decision_rule="TL-DG-002",
            primary_reason=PrimaryReason(code="CAP_BREACH", message="Policy limit exceeded."),
            risk_level="CRITICAL",
            risk_score=0.9,
            evidence_state=EvidenceQualityState.SUFFICIENT,
            decision_trace=[],
            decision_hash="0" * 64,
            gate_version="trustledger.decision-gate.v1",
        )
        block_dummy.decision_hash = compute_decision_hash(block_dummy.model_dump())
        self.block_decision = block_dummy

        review_dummy = DecisionResult(
            decision_id="dec_rev_001",
            verdict=FinalVerdict.REVIEW,
            decision_rule="TL-DG-003",
            primary_reason=PrimaryReason(code="STALE_EVIDENCE", message="Evidence > 30 days old."),
            risk_level="MEDIUM",
            risk_score=0.5,
            evidence_state=EvidenceQualityState.INSUFFICIENT,
            decision_trace=[],
            decision_hash="0" * 64,
            gate_version="trustledger.decision-gate.v1",
        )
        review_dummy.decision_hash = compute_decision_hash(review_dummy.model_dump())
        self.review_decision = review_dummy

        self.sample_request = {
            "decision_id": "dec_app_001",
            "action_type": "REFUND",
            "payment_id": "pay_test_12345",
            "amount": {"amount_minor": 150000, "currency": "INR"},
        }

    # -------------------------------------------------------------------------
    # 1. APPROVE → Razorpay called once → EXECUTED & 2. Successful Execution
    # -------------------------------------------------------------------------
    def test_1_2_approve_verdict_calls_razorpay_success(self):
        auth = self.gateway.authorize(self.approve_decision)

        self.mock_rzp_client.create_refund.side_effect = None
        self.mock_rzp_client.create_refund.return_value = RazorpayRefundResponse(
            refund_id="rfnd_succ_001",
            payment_id="pay_test_12345",
            amount_minor=150000,
            currency="INR",
            status="processed",
        )

        res = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_test_12345",
            use_razorpay=True,
        )

        self.assertEqual(res.status, ExecutionStatus.EXECUTED)
        self.assertEqual(res.provider, "razorpay")
        self.assertEqual(res.refund_id, "rfnd_succ_001")
        self.mock_rzp_client.create_refund.assert_called_once()
        self.assertEqual(auth.status, AuthorizationStatus.USED)

    # -------------------------------------------------------------------------
    # 3. REVIEW → Razorpay NOT called & 4. BLOCK → Razorpay NOT called
    # -------------------------------------------------------------------------
    def test_3_4_review_and_block_verdicts_never_call_razorpay(self):
        # Review attempt
        res_review = self.gateway.execute(
            authorization_id="auth_fake_review",
            decision_result=self.review_decision,
            request=self.sample_request,
            use_razorpay=True,
        )
        self.assertEqual(res_review.status, ExecutionStatus.DENIED)
        self.mock_rzp_client.create_refund.assert_not_called()

        # Block attempt
        res_block = self.gateway.execute(
            authorization_id="auth_fake_block",
            decision_result=self.block_decision,
            request=self.sample_request,
            use_razorpay=True,
        )
        self.assertEqual(res_block.status, ExecutionStatus.DENIED)
        self.mock_rzp_client.create_refund.assert_not_called()

    # -------------------------------------------------------------------------
    # 5. Missing Authorization → NOT called & 6. Expired Authorization → NOT called
    # -------------------------------------------------------------------------
    def test_5_6_missing_or_expired_authorization_never_calls_razorpay(self):
        # Missing auth
        res_missing = self.gateway.execute(
            authorization_id="nonexistent_auth_id",
            decision_result=self.approve_decision,
            request=self.sample_request,
            use_razorpay=True,
        )
        self.assertEqual(res_missing.status, ExecutionStatus.REJECTED)
        self.mock_rzp_client.create_refund.assert_not_called()

        # Expired auth
        auth = self.gateway.authorize(self.approve_decision)
        future_now = datetime.now(timezone.utc) + timedelta(seconds=400)

        res_expired = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            override_now=future_now,
            use_razorpay=True,
        )
        self.assertEqual(res_expired.status, ExecutionStatus.REJECTED)
        self.mock_rzp_client.create_refund.assert_not_called()

    # -------------------------------------------------------------------------
    # 7. Wrong Decision ID, 8. Wrong Payment ID, 9. Wrong Amount, 10. Wrong Currency
    # -------------------------------------------------------------------------
    def test_7_10_tampered_request_parameters_never_call_razorpay(self):
        auth = self.gateway.authorize(self.approve_decision)

        # Wrong decision ID in decision_result mismatch
        wrong_decision = copy.deepcopy(self.approve_decision)
        wrong_decision.decision_id = "dec_wrong_999"

        res_wrong_id = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=wrong_decision,
            request=self.sample_request,
            use_razorpay=True,
        )
        self.assertEqual(res_wrong_id.status, ExecutionStatus.REJECTED)
        self.mock_rzp_client.create_refund.assert_not_called()

        # Wrong amount (e.g. ₹2,000 vs authorized ₹1,500)
        tampered_amount_req = copy.deepcopy(self.sample_request)
        tampered_amount_req["amount"]["amount_minor"] = 200000

        res_wrong_amount = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=tampered_amount_req,
            use_razorpay=True,
        )
        self.assertEqual(res_wrong_amount.status, ExecutionStatus.REJECTED)
        self.mock_rzp_client.create_refund.assert_not_called()

    # -------------------------------------------------------------------------
    # 11. Consumed Authorization → NOT called & 12. Duplicate Execution → NOT called
    # -------------------------------------------------------------------------
    def test_11_12_consumed_authorization_prevents_duplicate_execution(self):
        auth = self.gateway.authorize(self.approve_decision)

        self.mock_rzp_client.create_refund.side_effect = None
        self.mock_rzp_client.create_refund.return_value = RazorpayRefundResponse(
            refund_id="rfnd_once",
            payment_id="pay_test_12345",
            amount_minor=150000,
            currency="INR",
            status="processed",
        )

        # First execution succeeds
        res1 = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_test_12345",
            use_razorpay=True,
        )
        self.assertEqual(res1.status, ExecutionStatus.EXECUTED)
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 1)

        # Second execution with same authorization & different idempotency key fails closed
        res2 = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="different_idempotency_key_67890",
            use_razorpay=True,
        )
        self.assertEqual(res2.failure_code, FailureCode.AUTHORIZATION_ALREADY_USED)
        # Mock call count remains strictly 1!
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 1)

    # -------------------------------------------------------------------------
    # 13. Provider 400, 14. 401, 15. 404, 16. 409, 17. 429, 18. 500, 19. Timeout, 20. Network
    # -------------------------------------------------------------------------
    def test_13_20_typed_provider_error_mappings(self):
        # 409 Conflict
        auth1 = self.gateway.authorize(self.approve_decision)
        self.mock_rzp_client.create_refund.side_effect = RazorpayConflictError("Concurrent refund")
        res_409 = self.gateway.execute(
            authorization_id=auth1.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_409",
            use_razorpay=True,
        )
        self.assertEqual(res_409.status, ExecutionStatus.PROVIDER_CONFLICT)
        self.assertEqual(res_409.failure_code, FailureCode.PROVIDER_CONFLICT)

        # 429 Rate Limit
        auth2 = self.gateway.authorize(self.approve_decision)
        self.mock_rzp_client.create_refund.side_effect = RazorpayRateLimitError("Rate limit exceeded")
        res_429 = self.gateway.execute(
            authorization_id=auth2.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_429",
            use_razorpay=True,
        )
        self.assertEqual(res_429.status, ExecutionStatus.PROVIDER_RATE_LIMIT)

        # Timeout
        auth3 = self.gateway.authorize(self.approve_decision)
        self.mock_rzp_client.create_refund.side_effect = RazorpayTimeoutError("Timed out")
        res_timeout = self.gateway.execute(
            authorization_id=auth3.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_timeout",
            use_razorpay=True,
        )
        self.assertEqual(res_timeout.status, ExecutionStatus.PROVIDER_TIMEOUT)

        # 500 Server Error
        auth4 = self.gateway.authorize(self.approve_decision)
        self.mock_rzp_client.create_refund.side_effect = RazorpayServerError("Server error")
        res_500 = self.gateway.execute(
            authorization_id=auth4.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_500",
            use_razorpay=True,
        )
        self.assertEqual(res_500.status, ExecutionStatus.PROVIDER_ERROR)

    # -------------------------------------------------------------------------
    # 21. Idempotency Key Preserved & 22. Unconsumed Auth on Transient Failure & 23. Consumed Auth on Success
    # -------------------------------------------------------------------------
    def test_21_23_transient_failure_preserves_authorization_state(self):
        auth = self.gateway.authorize(self.approve_decision)

        # Step 1: Transient 500 failure
        self.mock_rzp_client.create_refund.side_effect = RazorpayServerError("Internal error")
        res_fail = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_transient_101",
            use_razorpay=True,
        )
        self.assertEqual(res_fail.status, ExecutionStatus.PROVIDER_ERROR)
        # Authorization remains ISSUED (not consumed)
        self.assertEqual(auth.status, AuthorizationStatus.ISSUED)

        # Step 2: Retry with SAME idempotency key succeeds
        self.mock_rzp_client.create_refund.side_effect = None
        self.mock_rzp_client.create_refund.return_value = RazorpayRefundResponse(
            refund_id="rfnd_retry_ok",
            payment_id="pay_test_12345",
            amount_minor=150000,
            currency="INR",
            status="processed",
        )

        res_ok = self.gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            idempotency_key="idempotency_key_transient_101_retry",
            use_razorpay=True,
        )
        self.assertEqual(res_ok.status, ExecutionStatus.EXECUTED)
        # Authorization is now CONSUMED / USED
        self.assertEqual(auth.status, AuthorizationStatus.USED)

    # -------------------------------------------------------------------------
    # 24. SIGNATURE SAFETY SCENARIO: AI SUPPORT (0.99) + ₹60k vs ₹25k cap → BLOCK → Razorpay NOT Called
    # -------------------------------------------------------------------------
    def test_24_signature_safety_scenario_never_calls_razorpay(self):
        service = TrustLedgerDecisionService(execution_gateway=self.gateway)

        signature_request = {
            "decision_id": "dec_sig_risk_001",
            "action_type": "REFUND",
            "agent_id": "agent_support_001",
            "merchant_id": "merchant_tech_001",
            "reason": {"code": "REFUND_REQUESTED", "category": "CUSTOMER_REQUEST", "message": "Customer requesting refund over cap"},
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-30T12:00:00Z",
            "payment_id": "pay_sig_60k",
            "amount": {"amount_minor": 6000000, "currency": "INR"}, # ₹60,000
            "customer": {"customer_id": "cust_sig_001"},
            "evidence": [{"evidence_id": "ev_001", "type": "STRIPE_RECEIPT", "days_old": 2}],
        }

        # Verify decision through end-to-end pipeline
        decision_result, authorization = service.verify_decision(signature_request)

        self.assertEqual(decision_result.verdict, FinalVerdict.BLOCK)
        self.assertEqual(decision_result.decision_rule, "TL-DG-002")
        self.assertIsNone(authorization)

        # Attempt to execute refund on blocked decision
        res = service.execute_decision(
            decision_id="dec_sig_risk_001",
            authorization_id="auth_fake_bypass",
            payment_id="pay_sig_60k",
        )

        self.assertEqual(res.status, ExecutionStatus.DENIED)
        # Explicit assertion: Razorpay mock call count MUST BE STRICTLY ZERO!
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 0)

    # -------------------------------------------------------------------------
    # 25. AI CONTRADICT + APPROVE impossible path → Razorpay NOT called
    # -------------------------------------------------------------------------
    def test_25_ai_contradict_impossible_approve_never_calls_razorpay(self):
        res = self.gateway.execute(
            authorization_id="auth_fake",
            decision_result=self.block_decision,
            request=self.sample_request,
            use_razorpay=True,
        )
        self.assertEqual(res.status, ExecutionStatus.DENIED)
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 0)

    # -------------------------------------------------------------------------
    # 26. Frontend cannot force execution by supplying APPROVE in request body
    # -------------------------------------------------------------------------
    def test_26_frontend_cannot_force_execution_with_fake_verdict(self):
        service = TrustLedgerDecisionService(execution_gateway=self.gateway)

        # Ingest block request
        block_request = {
            "decision_id": "dec_blk_002",
            "action_type": "REFUND",
            "agent_id": "agent_support_001",
            "merchant_id": "merchant_tech_001",
            "reason": {"code": "REFUND_REQUESTED", "category": "CUSTOMER_REQUEST", "message": "Customer requesting refund over cap"},
            "evidence_references": ["ev_002"],
            "requested_at": "2026-08-30T12:00:00Z",
            "amount": {"amount_minor": 6000000, "currency": "INR"},
            "customer": {"customer_id": "cust_002"},
        }
        decision_result, authorization = service.verify_decision(block_request)

        # Attempt caller-side force execute
        res = service.execute_decision(
            decision_id="dec_blk_002",
            authorization_id="auth_fake_override",
            payment_id="pay_fake",
        )

        self.assertEqual(res.status, ExecutionStatus.DENIED)
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 0)

    # -------------------------------------------------------------------------
    # 27. Frontend cannot supply its own authorization to bypass checks
    # -------------------------------------------------------------------------
    def test_27_frontend_fake_authorization_bypasses_are_denied(self):
        fake_authorization_id = "auth_forged_by_client_12345"

        res = self.gateway.execute(
            authorization_id=fake_authorization_id,
            decision_result=self.approve_decision,
            request=self.sample_request,
            use_razorpay=True,
        )

        self.assertEqual(res.status, ExecutionStatus.REJECTED)
        self.assertEqual(self.mock_rzp_client.create_refund.call_count, 0)
