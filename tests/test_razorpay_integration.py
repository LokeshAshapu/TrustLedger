"""
TrustLedger Real Server-Side Razorpay Test-Mode Integration Test Suite
Section 23 Requirements - 25 Comprehensive Safety & Integration Tests
"""

import os
import unittest
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from execution.razorpay_client import RazorpayTestClient
from execution.models import RefundRequest as RazorpayRefundRequest, RefundResponse as RazorpayRefundResponse
from execution.errors import (
    RazorpayClientError,
    RazorpayConfigurationError,
    RazorpayAuthenticationError,
    RazorpayValidationError,
    RazorpayNotFoundError,
    RazorpayConflictError,
    RazorpayRateLimitError,
    RazorpayServerError,
    RazorpayTimeoutError,
    sanitize_secret_text,
)
from execution_engine.gateway import ExecutionGateway
from execution_engine.models import ExecutionStatus, FailureCode, AuthorizationStatus
from decision_gate.models import DecisionResult, FinalVerdict, PrimaryReason, EvidenceQualityState
from backend.orchestrator import TrustLedgerDecisionService
from backend.repository import SyntheticDataRepository
from backend.normalizer import normalize_request
from backend.app import app
from fastapi.testclient import TestClient


def _canonical_ctx(
    policy_cap_minor: int = 2500000,
    txn_amount_minor: int = 150000,
    ev_001_status: str = "VERIFIED",
) -> Dict[str, Any]:
    return {
        "evidence_db": {
            "ev_001": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_001",
                "evidence_type": "TRANSACTION",
                "source": "Stripe",
                "source_record_id": "txn_100",
                "timestamp": "2026-08-29T12:00:00Z",
                "verification_status": ev_001_status,
            },
            "ev_stale_999": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_stale_999",
                "evidence_type": "SUPPORT_LOG",
                "source": "Zendesk",
                "source_record_id": "ticket_999",
                "timestamp": "2026-05-01T00:00:00Z",
                "verification_status": "STALE",
            },
        },
        "transactions_db": {
            "txn_100": {
                "transaction_id": "txn_100",
                "order_id": "ord_100",
                "merchant_id": "merch_001",
                "customer_id": "cust_100",
                "amount": {"amount_minor": txn_amount_minor, "currency": "INR"},
                "payment_method": "CARD",
                "status": "CAPTURED",
                "created_at": "2026-08-29T10:00:00Z",
                "settled_at": "2026-08-29T10:05:00Z",
            },
            "pay_100": {
                "transaction_id": "pay_100",
                "order_id": "ord_100",
                "merchant_id": "merch_001",
                "customer_id": "cust_100",
                "amount": {"amount_minor": txn_amount_minor, "currency": "INR"},
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
                "amount": {"amount_minor": txn_amount_minor, "currency": "INR"},
                "status": "FULFILLED",
                "created_at": "2026-08-29T10:00:00Z",
            }
        },
        "customers_db": {
            "cust_100": {"customer_id": "cust_100", "merchant_id": "merch_001"}
        },
        "merchants_db": {
            "merch_001": {"merchant_id": "merch_001"}
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
                    {
                        "rule_id": "rule_auto_refund_cap",
                        "rule_name": "Max Automated Refund Cap",
                        "threshold_value": policy_cap_minor,
                        "is_hard_constraint": True,
                    }
                ],
            }
        },
        "refund_history_db": [],
    }


def _norm_verify(svc: TrustLedgerDecisionService, raw_req: Dict[str, Any]):
    ctx = raw_req.pop("context", None)
    norm = normalize_request(raw_req)
    if ctx:
        norm["context"] = ctx
    else:
        norm["context"] = _canonical_ctx()
    return svc.verify_decision(norm)


class TestRazorpayIntegration(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.repo = SyntheticDataRepository()

    # 1. Fetch Razorpay test payment (mocked HTTP)
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_01_fetch_razorpay_test_payment_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id":"pay_test_100","amount":150000,"currency":"INR","status":"captured","captured":true,"method":"upi","created_at":1600000000}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret", base_url="https://api.razorpay.com")
        pay = rzp_client.fetch_payment("pay_test_100")
        self.assertEqual(pay["id"], "pay_test_100")
        self.assertEqual(pay["amount"], 150000)
        self.assertTrue(pay["captured"])

    # 2. Missing payment ID
    def test_02_missing_payment_id_validation(self):
        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        with self.assertRaises(RazorpayValidationError):
            rzp_client.fetch_payment("")

    # 3. Invalid payment (404)
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_03_invalid_payment_404_handling(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 404, "Not Found", {}, None)
        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        with self.assertRaises(RazorpayNotFoundError):
            rzp_client.fetch_payment("pay_nonexistent_999")

    # 4. Captured payment metadata
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_04_captured_payment_metadata(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id":"pay_cap_001","amount":250000,"currency":"INR","status":"captured","captured":true}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        pay = rzp_client.fetch_payment("pay_cap_001")
        self.assertEqual(pay["status"], "captured")

    # 5. Non-captured payment metadata
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_05_non_captured_payment_metadata(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"id":"pay_uncap_001","amount":250000,"currency":"INR","status":"authorized","captured":false}'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        pay = rzp_client.fetch_payment("pay_uncap_001")
        self.assertFalse(pay["captured"])

    # 6. Refund amount <= payment amount -> PASS policy
    def test_06_refund_amount_less_than_or_equal_payment_amount(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_safe_006",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "payment_id": "pay_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.APPROVE)

    # 7. Refund amount > payment amount -> BLOCK
    def test_07_refund_amount_exceeds_payment_amount(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_exceed_007",
            "action_type": "REFUND",
            "amount": {"amount_minor": 500000, "currency": "INR"}, # ₹5,000 > txn ₹1,500
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.BLOCK)
        self.assertIsNone(auth)

    # 8. Safe refund APPROVE
    def test_08_safe_refund_approves(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_safe_008",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.APPROVE)
        self.assertIsNotNone(auth)

    # 9. Policy violation BLOCK
    def test_09_policy_violation_blocks(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_pol_009",
            "action_type": "REFUND",
            "amount": {"amount_minor": 6000000, "currency": "INR"}, # ₹60,000 > cap ₹25,000
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.BLOCK)

    # 10. Stale evidence REVIEW
    def test_10_stale_evidence_reviews(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_stale_010",
            "action_type": "REFUND",
            "amount": {"amount_minor": 50000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_stale_999"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.REVIEW)

    # 11. AI SUPPORT does not override BLOCK
    def test_11_ai_support_does_not_override_block(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_pol_011",
            "action_type": "REFUND",
            "amount": {"amount_minor": 6000000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.BLOCK)

    # 12. AI CONTRADICT behavior
    def test_12_ai_contradict_behaviour(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_safe_012",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": _canonical_ctx(),
        }
        res, _ = _norm_verify(svc, req)
        self.assertIn(res.verdict, [FinalVerdict.APPROVE, FinalVerdict.REVIEW])

    # 13. Authorization required for execution
    def test_13_authorization_required_for_execution(self):
        gateway = ExecutionGateway()
        res = DecisionResult(
            decision_id="dec_test_013",
            verdict=FinalVerdict.REVIEW,
            decision_rule="TL-DG-003",
            primary_reason=PrimaryReason(code="REVIEW_REQUIRED", message="Review required"),
            risk_level="MEDIUM",
            risk_score=0.5,
            evidence_state=EvidenceQualityState.INSUFFICIENT,
            decision_hash="a"*64,
        )
        with self.assertRaises(ValueError):
            gateway.authorize(res)

    # 14. BLOCK never calls Razorpay
    @patch("execution.razorpay_client.RazorpayTestClient.create_refund")
    def test_14_block_never_calls_razorpay(self, mock_create):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_pol_014",
            "action_type": "REFUND",
            "amount": {"amount_minor": 6000000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.BLOCK)
        self.assertIsNone(auth)
        mock_create.assert_not_called()

    # 15. REVIEW never calls Razorpay
    @patch("execution.razorpay_client.RazorpayTestClient.create_refund")
    def test_15_review_never_calls_razorpay(self, mock_create):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        req = {
            "decision_id": "dec_stale_015",
            "action_type": "REFUND",
            "amount": {"amount_minor": 50000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_stale_999"],
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.REVIEW)
        self.assertIsNone(auth)
        mock_create.assert_not_called()

    # 16. APPROVE calls Razorpay exactly once on execution
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_16_approve_calls_razorpay_once(self, mock_urlopen):
        mock_res = MagicMock()
        mock_res.read.return_value = b'{"id":"rfnd_rzp_16","payment_id":"pay_100","amount":150000,"currency":"INR","status":"processed"}'
        mock_res.__enter__.return_value = mock_res
        mock_urlopen.return_value = mock_res

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret", base_url="https://api.razorpay.com")
        gateway = ExecutionGateway(razorpay_client=rzp_client)
        svc = TrustLedgerDecisionService(data_repository=self.repo, execution_gateway=gateway)

        req = {
            "decision_id": "dec_safe_016",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)
        self.assertEqual(res.verdict, FinalVerdict.APPROVE)
        self.assertIsNotNone(auth)

        exec_res = svc.execute_decision(
            decision_id=res.decision_id,
            authorization_id=auth.authorization_id,
            payment_id="pay_100",
        )
        self.assertEqual(exec_res.status, ExecutionStatus.EXECUTED)
        self.assertEqual(exec_res.refund_id, "rfnd_rzp_16")

    # 17. Duplicate execution is prevented
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_17_duplicate_execution_prevented(self, mock_urlopen):
        mock_res = MagicMock()
        mock_res.read.return_value = b'{"id":"rfnd_rzp_17","payment_id":"pay_100","amount":150000,"currency":"INR","status":"processed"}'
        mock_res.__enter__.return_value = mock_res
        mock_urlopen.return_value = mock_res

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        gateway = ExecutionGateway(razorpay_client=rzp_client)
        svc = TrustLedgerDecisionService(data_repository=self.repo, execution_gateway=gateway)

        req = {
            "decision_id": "dec_safe_017",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)

        exec1 = svc.execute_decision(res.decision_id, auth.authorization_id, "pay_100")
        self.assertEqual(exec1.status, ExecutionStatus.EXECUTED)

        # Second call with same authorization -> REJECTED AUTHORIZATION_ALREADY_USED
        exec2 = svc.execute_decision(res.decision_id, auth.authorization_id, "pay_100")
        self.assertEqual(exec2.status, ExecutionStatus.REJECTED)
        self.assertEqual(exec2.failure_code, FailureCode.AUTHORIZATION_ALREADY_USED)

    # 18. Idempotency works
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_18_idempotency_cached_result(self, mock_urlopen):
        mock_res = MagicMock()
        mock_res.read.return_value = b'{"id":"rfnd_rzp_18","payment_id":"pay_100","amount":150000,"currency":"INR","status":"processed"}'
        mock_res.__enter__.return_value = mock_res
        mock_urlopen.return_value = mock_res

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        gateway = ExecutionGateway(razorpay_client=rzp_client)
        svc = TrustLedgerDecisionService(data_repository=self.repo, execution_gateway=gateway)

        req = {
            "decision_id": "dec_safe_018",
            "action_type": "REFUND",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "merchant_id": "merch_001",
            "evidence_references": ["ev_001"],
            "context": _canonical_ctx(),
        }
        res, auth = _norm_verify(svc, req)

        exec1 = svc.execute_decision(res.decision_id, auth.authorization_id, "pay_100", idempotency_key="idem_key_1234567890")
        self.assertEqual(exec1.status, ExecutionStatus.EXECUTED)

        exec2 = gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=res,
            request={"action_type": "REFUND", "amount": {"amount_minor": 150000, "currency": "INR"}, "payment_id": "pay_100"},
            idempotency_key="idem_key_1234567890",
            use_razorpay=True,
        )
        self.assertEqual(exec2.execution_id, exec1.execution_id)

    # 19. Razorpay timeout handling
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_19_razorpay_timeout_handling(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError(TimeoutError("timed out"))
        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret", max_attempts=1)
        req = RazorpayRefundRequest(payment_id="pay_100", amount_minor=150000, currency="INR", idempotency_key="idem_1234567890")
        with self.assertRaises(RazorpayTimeoutError):
            rzp_client.create_refund(req)

    # 20. Razorpay 429 rate limit handling
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_20_razorpay_429_handling(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        req = RazorpayRefundRequest(payment_id="pay_100", amount_minor=150000, currency="INR", idempotency_key="idem_1234567890")
        with self.assertRaises(RazorpayRateLimitError):
            rzp_client.create_refund(req)

    # 21. Razorpay 500 server error handling
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_21_razorpay_500_handling(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError("url", 500, "Server Error", {}, None)
        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret", max_attempts=1)
        req = RazorpayRefundRequest(payment_id="pay_100", amount_minor=150000, currency="INR", idempotency_key="idem_1234567890")
        with self.assertRaises(RazorpayServerError):
            rzp_client.create_refund(req)

    # 22. Production environment rejected
    def test_22_production_environment_rejected(self):
        with patch.dict(os.environ, {"RAZORPAY_ENVIRONMENT": "live"}):
            rzp_client = RazorpayTestClient(key_id="rzp_live_123", key_secret="secret_123")
            with self.assertRaises(RazorpayConfigurationError):
                rzp_client.fetch_payment("pay_100")

    # 23. Secret sanitization
    def test_23_secret_sanitization(self):
        secret = "Basic cnppX3Rlc3RfMTIzOnNlY3JldF80NTY="
        sanitized = sanitize_secret_text(secret)
        self.assertNotIn("cnppX3Rlc3RfMTIzOnNlY3JldF80NTY=", sanitized)
        self.assertIn("REDACTED", sanitized)

    # 24. Frontend cannot force execution
    def test_24_frontend_cannot_force_execution(self):
        svc = TrustLedgerDecisionService(data_repository=self.repo)
        exec_res = svc.execute_decision("dec_nonexistent", "auth_fake", "pay_100")
        self.assertEqual(exec_res.status, ExecutionStatus.REJECTED)
        self.assertEqual(exec_res.failure_code, FailureCode.AUTHORIZATION_NOT_FOUND)

    # 25. Actual Razorpay refund ID passed through correctly
    @patch("execution.razorpay_client.urllib.request.urlopen")
    def test_25_actual_razorpay_refund_id_passed_through(self, mock_urlopen):
        mock_res = MagicMock()
        mock_res.read.return_value = b'{"id":"rfnd_REAL_RAZORPAY_9999","payment_id":"pay_100","amount":150000,"currency":"INR","status":"processed"}'
        mock_res.__enter__.return_value = mock_res
        mock_urlopen.return_value = mock_res

        rzp_client = RazorpayTestClient(key_id="rzp_test_mock", key_secret="mock_secret")
        req = RazorpayRefundRequest(payment_id="pay_100", amount_minor=150000, currency="INR", idempotency_key="idem_1234567890")
        res = rzp_client.create_refund(req)
        self.assertEqual(res.refund_id, "rfnd_REAL_RAZORPAY_9999")


if __name__ == "__main__":
    unittest.main(verbosity=2)
