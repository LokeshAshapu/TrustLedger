"""
TrustLedger FastAPI REST API Endpoint Test Suite
Phase 10A End-to-End Backend Orchestration
"""

import unittest
from fastapi.testclient import TestClient
from backend.app import app


def get_canonical_context(policy_cap_minor: int = 2500000):
    return {
        "evidence_db": {
            "ev_001": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_001",
                "evidence_type": "TRANSACTION",
                "source": "Stripe",
                "source_record_id": "txn_100",
                "timestamp": "2026-08-29T12:00:00Z",
                "verification_status": "VERIFIED",
            }
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
                        "rule_name": "Refund Cap",
                        "threshold_value": policy_cap_minor,
                        "is_hard_constraint": True,
                    }
                ],
            }
        },
        "refund_history_db": [],
    }


class TestAPIV1(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "trustledger-orchestration-api")
        self.assertIn("components", data)

    def test_verify_decision_safe_approval(self):
        payload = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_api_safe_001",
            "action_type": "REFUND",
            "agent_id": "agent_api_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "order_id": "ord_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
            "reason": {
                "category": "NON_DELIVERY",
                "explanation": "Customer requested refund for item.",
            },
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": get_canonical_context(policy_cap_minor=2500000),
        }
        response = self.client.post("/api/v1/decisions/verify", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("decision_result", data)
        self.assertIn("verdict", data["decision_result"])
        self.assertEqual(data["decision_result"]["verdict"], "APPROVE")
        self.assertIsNotNone(data["authorization"])

    def test_verify_decision_signature_block(self):
        payload = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_api_block_002",
            "action_type": "REFUND",
            "agent_id": "agent_api_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "order_id": "ord_100",
            "amount": {"amount_minor": 6000000, "currency": "INR"}, # ₹60,000 > ₹25,000 limit
            "reason": {
                "category": "NON_DELIVERY",
                "explanation": "Customer requested refund for item.",
            },
            "evidence_references": ["ev_001"],
            "requested_at": "2026-08-29T12:00:00Z",
            "context": get_canonical_context(policy_cap_minor=2500000),
        }
        response = self.client.post("/api/v1/decisions/verify", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["decision_result"]["verdict"], "BLOCK")
        self.assertEqual(data["decision_result"]["decision_rule"], "TL-DG-002")
        self.assertIsNone(data["authorization"]) # No authorization token!

    def test_verify_decision_invalid_payload(self):
        # Missing action_type — normalizer returns structured 400 with field+message
        payload = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_invalid_003",
        }
        response = self.client.post("/api/v1/decisions/verify", json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        # New structured error format: {"error": "INVALID_REQUEST", "field": "action_type", "message": "..."}
        detail = data["detail"]
        self.assertIsInstance(detail, dict, "Error detail must be a structured object")
        self.assertEqual(detail["error"], "INVALID_REQUEST")
        self.assertEqual(detail["field"], "action_type")
        self.assertIn("action_type", detail["message"])
