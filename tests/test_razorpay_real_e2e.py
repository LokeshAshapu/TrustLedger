"""
TrustLedger Opt-In Real Razorpay Test-Mode E2E Test Suite
Section 24 Requirements — Executed ONLY if RUN_RAZORPAY_E2E=true and credentials exist.

To run:
  $env:RUN_RAZORPAY_E2E="true"
  python -m unittest tests/test_razorpay_real_e2e.py -v
"""

import os
import unittest
from execution.razorpay_client import RazorpayTestClient
from execution.models import RefundRequest as RazorpayRefundRequest
from execution.errors import RazorpayConfigurationError, sanitize_secret_text


class TestRazorpayRealE2E(unittest.TestCase):

    def setUp(self):
        run_e2e = os.getenv("RUN_RAZORPAY_E2E", "").lower() in ["true", "1", "yes"]
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        test_payment_id = os.getenv("RAZORPAY_TEST_PAYMENT_ID")
        env = os.getenv("RAZORPAY_ENVIRONMENT", "test").lower()

        if not run_e2e:
            raise unittest.SkipTest("Opt-in live Razorpay E2E test skipped. Set RUN_RAZORPAY_E2E=true to execute.")

        if env != "test":
            raise unittest.SkipTest(f"Live E2E test skipped: RAZORPAY_ENVIRONMENT is set to '{env}' (must be 'test').")

        if not key_id or not key_secret:
            raise unittest.SkipTest("Live E2E test skipped: RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET missing.")

        if not test_payment_id:
            raise unittest.SkipTest("Live E2E test skipped: RAZORPAY_TEST_PAYMENT_ID missing.")

        self.key_id = key_id
        self.key_secret = key_secret
        self.payment_id = test_payment_id
        self.client = RazorpayTestClient(key_id=key_id, key_secret=key_secret)

    def test_real_razorpay_test_mode_end_to_end_refund(self):
        """
        Performs real test-mode refund against Razorpay Test API.
        Verifies:
        1. Fetch payment metadata.
        2. Confirm payment is Test Mode & captured.
        3. Submit a small test refund (e.g. 100 paise = ₹1.00).
        4. Receive authentic Razorpay refund ID (rfnd_...).
        5. Verify idempotency on retry.
        """
        print(f"\n[RAZORPAY REAL E2E] Inspecting payment '{self.payment_id}' on Razorpay Test API...")

        # 1. Fetch Payment
        payment_info = self.client.fetch_payment(self.payment_id)
        self.assertEqual(payment_info["id"], self.payment_id)
        print(f"[RAZORPAY REAL E2E] Payment Status: {payment_info.get('status')}, Amount: {payment_info.get('amount')} paise")

        if not payment_info.get("captured"):
            raise unittest.SkipTest(f"Payment '{self.payment_id}' status is '{payment_info.get('status')}' (not captured). Cannot refund uncaptured payment.")

        # 2. Submit Real Test Refund
        idem_key = f"e2e_test_idem_{os.urandom(6).hex()}"
        req = RazorpayRefundRequest(
            payment_id=self.payment_id,
            amount_minor=100,  # ₹1.00 test refund
            currency="INR",
            idempotency_key=idem_key,
            notes={"test_source": "TrustLedger Real E2E Test"},
        )

        res = self.client.create_refund(req)
        print(f"[RAZORPAY REAL E2E] Success! Razorpay Refund ID: {res.refund_id}, Status: {res.status}")

        self.assertTrue(res.refund_id.startswith("rfnd_"), f"Refund ID must start with 'rfnd_'. Got: {res.refund_id}")
        self.assertEqual(res.payment_id, self.payment_id)
        self.assertEqual(res.amount_minor, 100)

        # 3. Verify Idempotency on exact same call
        res_repeat = self.client.create_refund(req)
        self.assertEqual(res_repeat.refund_id, res.refund_id, "Idempotency retry must return the same refund ID")
        print(f"[RAZORPAY REAL E2E] Idempotency verified for key '{idem_key}' -> Refund ID: {res_repeat.refund_id}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
