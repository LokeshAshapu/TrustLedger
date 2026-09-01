"""
TrustLedger Phase 11D — Razorpay Checkout & Automatic Payment Capture Integration Tests
"""

import os
import unittest
from fastapi.testclient import TestClient

from backend.app import app
from backend.orchestrator import TrustLedgerDecisionService
from execution.razorpay_client import RazorpayTestClient


class TestRazorpayCheckoutIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_create_razorpay_test_order_success(self):
        res = self.client.post(
            "/api/v1/razorpay/test/orders",
            json={
                "amount": 1500,
                "currency": "INR",
                "customer_name": "Demo Customer",
                "customer_email": "demo@example.com",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("order_id", data)
        self.assertTrue(data["order_id"].startswith("order_"))
        self.assertEqual(data["amount_rupees"], 1500.0)
        self.assertEqual(data["amount_minor"], 150000)
        self.assertEqual(data["currency"], "INR")
        self.assertIn("key_id", data)

    def test_02_create_razorpay_test_order_invalid_amount(self):
        res = self.client.post(
            "/api/v1/razorpay/test/orders",
            json={"amount": 0, "currency": "INR"},
        )
        self.assertEqual(res.status_code, 400)

    def test_03_verify_payment_signature_success(self):
        # 1. Create order
        order_res = self.client.post(
            "/api/v1/razorpay/test/orders",
            json={"amount": 1500, "currency": "INR"},
        ).json()

        order_id = order_res["order_id"]
        payment_id = "pay_test_checkout_100"

        # 2. Verify signature
        verify_res = self.client.post(
            "/api/v1/razorpay/test/payment/verify",
            json={
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_id,
                "razorpay_signature": "sig_valid_test_mock",
                "amount": 1500,
                "currency": "INR",
            },
        )
        self.assertEqual(verify_res.status_code, 200)
        vdata = verify_res.json()
        self.assertTrue(vdata["verified"])
        self.assertEqual(vdata["payment_id"], payment_id)
        self.assertEqual(vdata["amount_rupees"], 1500.0)

    def test_04_verify_payment_signature_invalid(self):
        res = self.client.post(
            "/api/v1/razorpay/test/payment/verify",
            json={
                "razorpay_payment_id": "pay_tampered_100",
                "razorpay_order_id": "order_tampered_100",
                "razorpay_signature": "",  # Empty signature
                "amount": 1500,
            },
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["detail"]["error"], "INVALID_PAYMENT_SIGNATURE")

    def test_05_end_to_end_safe_refund_flow_approve(self):
        # Step 1: Create Order
        order_data = self.client.post(
            "/api/v1/razorpay/test/orders",
            json={"amount": 1500, "currency": "INR"},
        ).json()

        payment_id = "pay_safe_e2e_001"

        # Step 2: Verify Payment
        self.client.post(
            "/api/v1/razorpay/test/payment/verify",
            json={
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": order_data["order_id"],
                "razorpay_signature": "sig_valid_test_mock",
                "amount": 1500,
            },
        )

        # Step 3: Verify Refund Request through Decision Gate
        decision_res = self.client.post(
            "/api/v1/decisions/verify",
            json={
                "decision_id": "demo-e2e-safe-001",
                "action_type": "REFUND",
                "amount": 500,
                "currency": "INR",
                "customer_id": "cust_100",
                "merchant_id": "merch_001",
                "transaction_id": payment_id,
                "payment_id": payment_id,
                "evidence_references": ["ev_001"],
            },
        )
        self.assertEqual(decision_res.status_code, 200)
        ddata = decision_res.json()
        dr = ddata["decision_result"]
        auth = ddata["authorization"]
        self.assertEqual(dr["verdict"], "APPROVE")
        self.assertIsNotNone(auth)

        # Step 4: Execute Refund
        exec_res = self.client.post(
            f"/api/v1/decisions/{dr['decision_id']}/execute",
            json={
                "authorization_id": auth["authorization_id"],
                "payment_id": payment_id,
            },
        )
        self.assertEqual(exec_res.status_code, 200)
        edata = exec_res.json()
        self.assertTrue(edata["success"])

    def test_06_policy_cap_block_cannot_execute(self):
        payment_id = "pay_block_cap_001"

        self.client.post(
            "/api/v1/razorpay/test/payment/verify",
            json={
                "razorpay_payment_id": payment_id,
                "razorpay_order_id": "order_cap_001",
                "razorpay_signature": "sig_valid_test_mock",
                "amount": 60000,
            },
        )

        decision_res = self.client.post(
            "/api/v1/decisions/verify",
            json={
                "decision_id": "demo-cap-block-001",
                "action_type": "REFUND",
                "amount": 60000,
                "currency": "INR",
                "customer_id": "cust_100",
                "merchant_id": "merch_001",
                "transaction_id": payment_id,
                "payment_id": payment_id,
                "evidence_references": ["ev_001"],
            },
        )
        self.assertEqual(decision_res.status_code, 200)
        ddata = decision_res.json()
        dr = ddata["decision_result"]
        auth = ddata.get("authorization")
        self.assertEqual(dr["verdict"], "BLOCK")
        self.assertIsNone(auth)


if __name__ == "__main__":
    unittest.main()
