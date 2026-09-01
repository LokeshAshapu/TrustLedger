"""
TrustLedger Razorpay Test-Mode Client Test Suite
Phase 11B.1 Razorpay Test-Mode Refund Client
"""

import os
import json
import unittest
import urllib.error
from unittest.mock import patch, MagicMock

from execution.models import RefundRequest, RefundResponse
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
    RazorpayNetworkError,
    sanitize_secret_text,
)
from execution.razorpay_client import RazorpayTestClient


class TestRazorpayClientSuite(unittest.TestCase):

    def setUp(self):
        self.fake_key_id = "rzp_test_fake123456"
        self.fake_key_secret = "secret_fake_9876543210"
        self.client = RazorpayTestClient(
            key_id=self.fake_key_id,
            key_secret=self.fake_key_secret,
            base_url="https://api.razorpay.com",
            timeout_seconds=5.0,
            max_attempts=2,
        )

    # -------------------------------------------------------------------------
    # 1. VALID REFUND REQUEST & RESPONSE NORMALIZATION
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_1_valid_refund_request_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "rfnd_test_1001",
            "entity": "refund",
            "amount": 150000,
            "currency": "INR",
            "payment_id": "pay_L123456789",
            "status": "processed",
            "receipt": "rcpt_001",
            "notes": {"reason": "Non-delivery"},
            "created_at": 1700000000,
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        req = RefundRequest(
            payment_id="pay_L123456789",
            amount_minor=150000, # ₹1,500
            currency="INR",
            idempotency_key="idempotency_key_test_12345",
            receipt="rcpt_001",
            notes={"reason": "Non-delivery"},
        )

        res = self.client.create_refund(req)

        self.assertEqual(res.refund_id, "rfnd_test_1001")
        self.assertEqual(res.payment_id, "pay_L123456789")
        self.assertEqual(res.amount_minor, 150000)
        self.assertEqual(res.currency, "INR")
        self.assertEqual(res.status, "processed")

        # Inspect headers passed to urllib
        args, kwargs = mock_urlopen.call_args
        request_obj = args[0]
        self.assertEqual(request_obj.get_header("X-refund-idempotency"), "idempotency_key_test_12345")
        self.assertTrue(request_obj.get_header("Authorization").startswith("Basic "))

    # -------------------------------------------------------------------------
    # 2. INR MINOR-UNIT HANDLING (PAISE)
    # -------------------------------------------------------------------------
    def test_2_inr_minor_unit_paise_conversion(self):
        req = RefundRequest(
            payment_id="pay_999",
            amount_minor=6000000, # ₹60,000 in paise
            idempotency_key="idempotency_key_test_12345",
        )
        self.assertEqual(req.amount_minor, 6000000)

    # -------------------------------------------------------------------------
    # 3. INVALID PAYMENT ID VALIDATION
    # -------------------------------------------------------------------------
    def test_3_invalid_payment_id_rejection(self):
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="", amount_minor=1000, idempotency_key="idempotency_key_12345")

    # -------------------------------------------------------------------------
    # 4. ZERO AMOUNT REJECTION
    # -------------------------------------------------------------------------
    def test_4_zero_amount_rejection(self):
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=0, idempotency_key="idempotency_key_12345")

    # -------------------------------------------------------------------------
    # 5. NEGATIVE AMOUNT REJECTION
    # -------------------------------------------------------------------------
    def test_5_negative_amount_rejection(self):
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=-500, idempotency_key="idempotency_key_12345")

    # -------------------------------------------------------------------------
    # 6. FLOAT AMOUNT REJECTION
    # -------------------------------------------------------------------------
    def test_6_float_amount_rejection(self):
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=150.50, idempotency_key="idempotency_key_12345") # type: ignore

    # -------------------------------------------------------------------------
    # 7. INVALID CURRENCY VALIDATION
    # -------------------------------------------------------------------------
    def test_7_invalid_currency_rejection(self):
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=1000, currency="inr", idempotency_key="idempotency_key_12345")

    # -------------------------------------------------------------------------
    # 8. INVALID IDEMPOTENCY KEY VALIDATION
    # -------------------------------------------------------------------------
    def test_8_invalid_idempotency_key_rejection(self):
        # Too short (< 10 chars)
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="short")

        # Invalid special chars
        with self.assertRaises(ValueError):
            RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="invalid!key@12345")

    # -------------------------------------------------------------------------
    # 9. MISSING CREDENTIALS FAIL-CLOSED EXCEPTION
    # -------------------------------------------------------------------------
    def test_9_missing_credentials_fails_closed(self):
        empty_client = RazorpayTestClient(key_id="", key_secret="")
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayConfigurationError):
            empty_client.create_refund(req)

    # -------------------------------------------------------------------------
    # 10. AUTHENTICATION FAILURE (HTTP 401)
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_10_authentication_failure_401(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_001/refund",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayAuthenticationError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 401)

    # -------------------------------------------------------------------------
    # 11. HTTP 400 PROVIDER ERROR
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_11_bad_request_400(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_001/refund",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayValidationError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 400)

    # -------------------------------------------------------------------------
    # 12. HTTP 404 NOT FOUND
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_12_not_found_404(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_nonexistent/refund",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_nonexistent", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayNotFoundError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 404)

    # -------------------------------------------------------------------------
    # 13. HTTP 409 IDEMPOTENCY CONFLICT
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_13_idempotency_conflict_409(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_001/refund",
            code=409,
            msg="Conflict",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayConflictError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 409)

    # -------------------------------------------------------------------------
    # 14. HTTP 429 RATE LIMIT
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_14_rate_limit_429(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_001/refund",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayRateLimitError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 429)

    # -------------------------------------------------------------------------
    # 15. HTTP 500 SERVER ERROR
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_15_server_error_500(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://api.razorpay.com/v1/payments/pay_001/refund",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayServerError) as cm:
            self.client.create_refund(req)
        self.assertEqual(cm.exception.status_code, 500)

    # -------------------------------------------------------------------------
    # 16. NETWORK TIMEOUT ERROR
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_16_network_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(reason=TimeoutError("timed out"))
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayTimeoutError):
            self.client.create_refund(req)

    # -------------------------------------------------------------------------
    # 17. CONNECTION FAILURE
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_17_connection_failure(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(reason="Connection refused")
        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_12345")

        with self.assertRaises(RazorpayNetworkError):
            self.client.create_refund(req)

    # -------------------------------------------------------------------------
    # 18. BOUNDED RETRY BEHAVIOR (MAX 2 ATTEMPTS) & 19. PRESERVE IDEMPOTENCY KEY
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_18_19_bounded_retry_preserves_idempotency_key(self, mock_urlopen):
        # Attempt 1 fails with 503, Attempt 2 succeeds
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "rfnd_retry_succ",
            "payment_id": "pay_001",
            "amount": 1000,
            "currency": "INR",
            "status": "processed",
        }).encode("utf-8")

        mock_urlopen.side_effect = [
            urllib.error.HTTPError(url="...", code=503, msg="Service Unavailable", hdrs={}, fp=None),
            MagicMock(__enter__=MagicMock(return_value=mock_response)),
        ]

        req = RefundRequest(payment_id="pay_001", amount_minor=1000, idempotency_key="idempotency_key_retry_99")
        res = self.client.create_refund(req)

        self.assertEqual(res.refund_id, "rfnd_retry_succ")
        self.assertEqual(mock_urlopen.call_count, 2)

        # Confirm idempotency key was preserved on retry
        second_call_args = mock_urlopen.call_args_list[1][0]
        request_obj = second_call_args[0]
        self.assertEqual(request_obj.get_header("X-refund-idempotency"), "idempotency_key_retry_99")

    # -------------------------------------------------------------------------
    # 20. SECRET SANITIZATION IN EXCEPTIONS
    # -------------------------------------------------------------------------
    def test_20_secret_sanitization_in_exceptions(self):
        secret_msg = f"Failed call with key {self.fake_key_secret} and header Basic cnpwX3Rlc3Q6c2VjcmV0"
        err = RazorpayClientError(secret_msg)
        err_str = str(err)

        self.assertNotIn(self.fake_key_secret, err_str)
        self.assertIn("REDACTED", err_str)

    # -------------------------------------------------------------------------
    # 21. SECRET SANITIZATION UTILITY
    # -------------------------------------------------------------------------
    def test_21_secret_sanitization_utility(self):
        raw = "Error using rzp_test_123456789 and Authorization: Basic QWxhZGRpbjpPcGVuU2VzYW1l"
        clean = sanitize_secret_text(raw)
        self.assertNotIn("rzp_test_123456789", clean)
        self.assertNotIn("QWxhZGRpbjpPcGVuU2VzYW1l", clean)
        self.assertIn("REDACTED", clean)

    # -------------------------------------------------------------------------
    # 22. FETCH REFUND BY ID
    # -------------------------------------------------------------------------
    @patch("urllib.request.urlopen")
    def test_22_fetch_refund_by_id(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "id": "rfnd_fetch_001",
            "payment_id": "pay_001",
            "amount": 1000,
            "currency": "INR",
            "status": "processed",
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = self.client.fetch_refund("rfnd_fetch_001")
        self.assertEqual(res.refund_id, "rfnd_fetch_001")
        self.assertEqual(res.payment_id, "pay_001")

    # -------------------------------------------------------------------------
    # 23. OPT-IN CONDITIONAL LIVE SMOKE TEST
    # -------------------------------------------------------------------------
    def test_live_razorpay_smoke_test(self):
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        test_payment_id = os.getenv("RAZORPAY_TEST_PAYMENT_ID")

        if not key_id or not key_secret or not test_payment_id:
            self.skipTest(
                "RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, or RAZORPAY_TEST_PAYMENT_ID not present in environment. "
                "Skipping live opt-in smoke test."
            )

        live_client = RazorpayTestClient()
        req = RefundRequest(
            payment_id=test_payment_id,
            amount_minor=100, # ₹1.00 paise
            idempotency_key=f"smoke_test_{int(os.getenv('BUILD_NUMBER', '100'))}_{os.urandom(4).hex()}",
        )

        res = live_client.create_refund(req)
        print("\n" + "=" * 70)
        print("OPT-IN LIVE RAZORPAY TEST-MODE SMOKE TEST RESULT")
        print("=" * 70)
        print(f"Refund ID:       {res.refund_id}")
        print(f"Payment ID:      {res.payment_id}")
        print(f"Amount Minor:    {res.amount_minor} ({res.currency})")
        print(f"Status:          {res.status}")
        print("=" * 70)

        self.assertIsNotNone(res.refund_id)
