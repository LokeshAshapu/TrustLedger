"""
TrustLedger Real Test-Mode Razorpay Checkout E2E Test
Opt-in live network test file for Razorpay Test API.
Set RUN_RAZORPAY_E2E=true to execute.
"""

import os
import unittest
from execution.razorpay_client import RazorpayTestClient


class TestRazorpayCheckoutRealE2E(unittest.TestCase):
    def setUp(self):
        self.run_e2e = os.getenv("RUN_RAZORPAY_E2E", "false").lower() == "true"
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not self.run_e2e or not self.key_id or not self.key_secret:
            self.skipTest(
                "Opt-in live Razorpay Checkout E2E test skipped. "
                "Set RUN_RAZORPAY_E2E=true and configure RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET to execute."
            )

        self.client = RazorpayTestClient(
            key_id=self.key_id,
            key_secret=self.key_secret,
            environment="test",
        )

    def test_real_razorpay_order_creation(self):
        order = self.client.create_order(
            amount_minor=150000,
            currency="INR",
            receipt="rcpt_e2e_checkout_100",
            notes={"environment": "test", "test_case": "real_checkout_e2e"},
        )
        self.assertIsNotNone(order)
        self.assertIn("id", order)
        self.assertTrue(order["id"].startswith("order_"))
        self.assertEqual(order["amount"], 150000)
        self.assertEqual(order["currency"], "INR")


if __name__ == "__main__":
    unittest.main()
