"""
TrustLedger Real Razorpay Test-Mode End-to-End Validation Test Suite
Phase 11B.3 Real Razorpay Test-Mode E2E Validation

IMPORTANT: Real Razorpay API network calls occur ONLY when RUN_RAZORPAY_E2E=true.
By default during standard test discovery (python -m unittest discover tests/ "test_*.py"),
this entire test suite is safely SKIPPED.
"""

import os
import time
import unittest
from datetime import datetime, timezone

from decision_gate.models import FinalVerdict
from execution_engine.models import ExecutionStatus, AuthorizationStatus
from execution.razorpay_client import RazorpayTestClient
from execution.errors import RazorpayConfigurationError, RazorpayClientError
from backend.orchestrator import TrustLedgerDecisionService
from backend.repository import SyntheticDataRepository


class TestRazorpayE2EIntegration(unittest.TestCase):
    """
    Live End-to-End Integration Suite against REAL Razorpay Test Mode API.
    Validates complete pipeline from DecisionRequest -> DecisionGate -> ExecutionAuthorization -> Razorpay.
    """

    @classmethod
    def setUpClass(cls):
        cls.run_e2e = os.getenv("RUN_RAZORPAY_E2E", "false").lower() == "true"
        cls.key_id = os.getenv("RAZORPAY_KEY_ID")
        cls.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        cls.payment_id = os.getenv("RAZORPAY_TEST_PAYMENT_ID")
        cls.environment = os.getenv("RAZORPAY_ENVIRONMENT", "test").lower()

        if not cls.run_e2e or not cls.key_id or not cls.key_secret or not cls.payment_id:
            raise unittest.SkipTest(
                "LIVE RAZORPAY TEST MODE SKIPPED: RUN_RAZORPAY_E2E!=true or missing required environment variables "
                "(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_TEST_PAYMENT_ID)."
            )

        if cls.environment != "test":
            raise unittest.SkipTest(
                f"LIVE RAZORPAY TEST MODE SKIPPED: RAZORPAY_ENVIRONMENT is '{cls.environment}'. "
                "Only Test Mode execution is permitted."
            )

        print("\n==================================================")
        print("     LIVE RAZORPAY TEST MODE E2E VALIDATION      ")
        print("==================================================")
        print(f"Target Base URL: {os.getenv('RAZORPAY_BASE_URL', 'https://api.razorpay.com')}")
        print(f"Target Environment: {cls.environment}")
        print(f"Test Payment ID: {cls.payment_id}")

    def setUp(self):
        self.rzp_client = RazorpayTestClient(
            key_id=self.key_id,
            key_secret=self.key_secret,
            base_url=os.getenv("RAZORPAY_BASE_URL", "https://api.razorpay.com"),
        )
        self.repository = SyntheticDataRepository()
        self.service = TrustLedgerDecisionService(
            data_repository=self.repository,
            execution_gateway=None, # uses default gateway with default razorpay_client
        )
        self.service.execution_gateway.razorpay_client = self.rzp_client

    # -------------------------------------------------------------------------
    # 1. Preflight Health & Payment Inspection (Non-Mutating)
    # -------------------------------------------------------------------------
    def test_1_razorpay_preflight_health_check(self):
        print("\n[LIVE E2E] Running Preflight Health Check...")

        health = self.rzp_client.health_check()
        self.assertEqual(health["environment"], "test")
        self.assertTrue(health["configured"])

        # Fetch payment via read-only API to verify payment eligibility
        payment = self.rzp_client.fetch_payment(self.payment_id)
        self.assertIsNotNone(payment)
        self.assertEqual(payment.get("id"), self.payment_id)
        self.assertIn("amount", payment)

        print(f"[LIVE E2E] Preflight payment verified: id='{payment.get('id')}' amount={payment.get('amount')} minor currency='{payment.get('currency')}' status='{payment.get('status')}'")

    # -------------------------------------------------------------------------
    # 2. Complete APPROVE Path -> Real Razorpay Test Refund Execution
    # -------------------------------------------------------------------------
    def test_2_end_to_end_approve_refund_execution(self):
        print("\n[LIVE E2E] Executing End-to-End APPROVE Refund Scenario...")

        # Safe refund amount: 100 minor units (₹1.00)
        refund_amount_minor = 100
        idempotency_key = f"idempotency_e2e_{int(time.time())}"

        # 1. Construct valid canonical refund request eligible for APPROVE
        approve_request = {
            "decision_id": f"dec_e2e_approve_{int(time.time())}",
            "action_type": "REFUND",
            "agent_id": "agent_support_001",
            "merchant_id": "merchant_tech_001",
            "reason": {
                "code": "CUSTOMER_REQUEST",
                "category": "CUSTOMER_REQUEST",
                "message": "Valid customer request eligible for test refund",
            },
            "evidence_references": ["ev_e2e_001"],
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "amount": {"amount_minor": refund_amount_minor, "currency": "INR"},
            "customer": {"customer_id": "cust_e2e_001"},
            "evidence": [
                {
                    "evidence_id": "ev_e2e_001",
                    "type": "STRIPE_RECEIPT",
                    "days_old": 2,
                }
            ],
        }

        # 2. Run decision pipeline
        decision_result, authorization = self.service.verify_decision(approve_request)

        # Assert decision verdict is APPROVE
        self.assertEqual(decision_result.verdict, FinalVerdict.APPROVE)
        self.assertIsNotNone(authorization)
        self.assertEqual(authorization.status, AuthorizationStatus.ISSUED)

        # 3. Execute authorized refund via Razorpay Test Client
        exec_result = self.service.execute_decision(
            decision_id=approve_request["decision_id"],
            authorization_id=authorization.authorization_id,
            payment_id=self.payment_id,
            idempotency_key=idempotency_key,
        )

        # Assert real Razorpay execution result
        self.assertEqual(exec_result.status, ExecutionStatus.EXECUTED)
        self.assertEqual(exec_result.provider, "razorpay")
        self.assertTrue(exec_result.refund_id.startswith("rfnd_"))
        self.assertEqual(exec_result.payment_id, self.payment_id)

        print(f"[LIVE E2E] Real Razorpay Test Refund Executed Successfully!")
        print(f"           Refund ID: {exec_result.refund_id}")
        print(f"           Payment ID: {exec_result.payment_id}")
        print(f"           Amount: {exec_result.amount.amount_minor} minor units ({exec_result.amount.currency})")

        # 4. Idempotency Check: Re-attempt execution with SAME idempotency key
        retry_exec = self.service.execute_decision(
            decision_id=approve_request["decision_id"],
            authorization_id=authorization.authorization_id,
            payment_id=self.payment_id,
            idempotency_key=idempotency_key,
        )

        self.assertEqual(retry_exec.execution_id, exec_result.execution_id)
        self.assertEqual(retry_exec.refund_id, exec_result.refund_id)
        print(f"[LIVE E2E] Idempotency Verified: Cached response returned for key '{idempotency_key}'")

    # -------------------------------------------------------------------------
    # 3. REVIEW Safety Case -> Razorpay MUST NOT BE CALLED
    # -------------------------------------------------------------------------
    def test_3_end_to_end_review_safety_scenario(self):
        print("\n[LIVE E2E] Executing REVIEW Safety Scenario...")

        # Request with stale evidence (35 days old) triggers REVIEW verdict
        review_request = {
            "decision_id": f"dec_e2e_review_{int(time.time())}",
            "action_type": "REFUND",
            "agent_id": "agent_support_001",
            "merchant_id": "merchant_tech_001",
            "reason": {
                "code": "CUSTOMER_REQUEST",
                "category": "CUSTOMER_REQUEST",
                "message": "Refund request with stale evidence",
            },
            "evidence_references": ["ev_stale_001"],
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "customer": {"customer_id": "cust_stale_001"},
            "evidence": [
                {
                    "evidence_id": "ev_stale_001",
                    "type": "STRIPE_RECEIPT",
                    "days_old": 35, # > 30 days -> STALE_EVIDENCE -> REVIEW
                }
            ],
        }

        decision_result, authorization = self.service.verify_decision(review_request)

        self.assertEqual(decision_result.verdict, FinalVerdict.REVIEW)
        self.assertIsNone(authorization)

        # Attempt force-execute
        exec_result = self.service.execute_decision(
            decision_id=review_request["decision_id"],
            authorization_id="auth_forged_review_bypass",
            payment_id=self.payment_id,
        )

        self.assertEqual(exec_result.status, ExecutionStatus.DENIED)
        print("[LIVE E2E] REVIEW Safety Case Verified: Authorization denied, Razorpay NOT called.")

    # -------------------------------------------------------------------------
    # 4. BLOCK Safety Case -> Razorpay MUST NOT BE CALLED
    # -------------------------------------------------------------------------
    def test_4_end_to_end_block_safety_scenario(self):
        print("\n[LIVE E2E] Executing BLOCK Safety Scenario (Signature Scenario)...")

        # Signature scenario: AI SUPPORT (0.99) + ₹60,000 refund vs ₹25,000 policy cap -> BLOCK
        block_request = {
            "decision_id": f"dec_e2e_block_{int(time.time())}",
            "action_type": "REFUND",
            "agent_id": "agent_support_001",
            "merchant_id": "merchant_tech_001",
            "reason": {
                "code": "CUSTOMER_REQUEST",
                "category": "CUSTOMER_REQUEST",
                "message": "High-value refund request exceeding policy cap",
            },
            "evidence_references": ["ev_high_001"],
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "amount": {"amount_minor": 6000000, "currency": "INR"}, # ₹60,000
            "customer": {"customer_id": "cust_high_001"},
            "evidence": [
                {
                    "evidence_id": "ev_high_001",
                    "type": "STRIPE_RECEIPT",
                    "days_old": 2,
                }
            ],
        }

        decision_result, authorization = self.service.verify_decision(block_request)

        self.assertEqual(decision_result.verdict, FinalVerdict.BLOCK)
        self.assertEqual(decision_result.decision_rule, "TL-DG-002")
        self.assertIsNone(authorization)

        # Attempt force-execute
        exec_result = self.service.execute_decision(
            decision_id=block_request["decision_id"],
            authorization_id="auth_forged_block_bypass",
            payment_id=self.payment_id,
        )

        self.assertEqual(exec_result.status, ExecutionStatus.DENIED)
        print("[LIVE E2E] BLOCK Safety Case Verified: Authorization denied (TL-DG-002), Razorpay NOT called.")
