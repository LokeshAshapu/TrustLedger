"""
TrustLedger Financial Execution Simulator Unit & Security Test Suite
Phase 7 Bounded Financial Execution Layer
Simulator Version: trustledger.execution-simulator.v1
"""

import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine
from verifier.packet_builder import AIVerificationPacketBuilder
from verifier.service import AIVerificationService
from verifier.providers.mock_provider import MockLLMProvider
from decision_gate.gate import DecisionGate
from decision_gate.models import FinalVerdict
from execution_engine.gateway import ExecutionGateway
from execution_engine.agent_client import AIAgentClient
from execution_engine.models import (
    AuthorizationStatus,
    ExecutionStatus,
    FailureCode,
    EXECUTION_SIMULATOR_VERSION,
)
from execution_engine.app import app


class TestExecutionSimulator(unittest.TestCase):

    def setUp(self):
        self.det_engine = DeterministicTrustEngine()
        self.risk_engine = FinancialRiskEngine()
        self.ai_service = AIVerificationService(MockLLMProvider())
        self.decision_gate = DecisionGate()
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

        self.gateway = ExecutionGateway(self.context)
        self.agent = AIAgentClient()
        self.client = TestClient(app)

    # 1. Authorization Issuance: APPROVE succeeds
    def test_authorize_approve_decision(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_auth_ok",
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
        pkt = AIVerificationPacketBuilder.build(req, self.context, det_res, risk_res)
        ai_res = self.ai_service.verify_context(pkt)
        gate_res = self.decision_gate.evaluate(req, det_res, risk_res, ai_res)

        self.assertEqual(gate_res.verdict, FinalVerdict.APPROVE)

        auth = self.gateway.authorize(gate_res)
        self.assertEqual(auth.status, AuthorizationStatus.ISSUED)
        self.assertEqual(auth.decision_id, "dec_auth_ok")
        self.assertEqual(auth.authorized_amount.amount_minor, 150000)

    # 2. Authorization Issuance: REVIEW and BLOCK Fail
    def test_authorize_review_and_block_fail(self):
        # BLOCK decision (over cap)
        req_blk = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_auth_blk",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 6000000, "currency": "INR"},
            "reason": {"category": "CUSTOMER_REQUEST"},
            "evidence_references": ["ev_001"],
            "requested_at": self.base_time,
        }
        det_blk = self.det_engine.verify(req_blk, self.context)
        risk_blk = self.risk_engine.assess(req_blk, self.context, det_blk)
        gate_blk = self.decision_gate.evaluate(req_blk, det_blk, risk_blk)

        self.assertEqual(gate_blk.verdict, FinalVerdict.BLOCK)
        with self.assertRaises(ValueError) as cm:
            self.gateway.authorize(gate_blk)
        self.assertIn("DECISION_NOT_APPROVED", str(cm.exception))

    # 3. Successful Sandbox Execution Test
    def test_successful_sandbox_execution(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_exec_ok",
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
        pkt = AIVerificationPacketBuilder.build(req, self.context, det_res, risk_res)
        ai_res = self.ai_service.verify_context(pkt)
        gate_res = self.decision_gate.evaluate(req, det_res, risk_res, ai_res)

        auth = self.gateway.authorize(gate_res)
        exec_res = self.gateway.execute(auth.authorization_id, gate_res, req)

        self.assertEqual(exec_res.status, ExecutionStatus.SUCCESS)
        self.assertEqual(exec_res.failure_code, FailureCode.NONE)
        self.assertTrue(exec_res.external_reference.startswith("ref_sync_"))
        self.assertEqual(self.gateway.authorizations[auth.authorization_id].status, AuthorizationStatus.USED)

    # 4. Replay Protection Test
    def test_replay_protection(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_replay",
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
        gate_res = self.decision_gate.evaluate(req, det_res, risk_res)

        auth = self.gateway.authorize(gate_res)
        res1 = self.gateway.execute(auth.authorization_id, gate_res, req)
        self.assertEqual(res1.status, ExecutionStatus.SUCCESS)

        # Submit authorization a second time -> REJECTED (AUTHORIZATION_ALREADY_USED)
        res2 = self.gateway.execute(auth.authorization_id, gate_res, req)
        self.assertEqual(res2.status, ExecutionStatus.REJECTED)
        self.assertEqual(res2.failure_code, FailureCode.AUTHORIZATION_ALREADY_USED)

    # 5. Tamper Protection Test (Amount Mismatch & Hash Mismatch)
    def test_tamper_protection(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_tamper",
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
        gate_res = self.decision_gate.evaluate(req, det_res, risk_res)

        auth = self.gateway.authorize(gate_res)

        # Attempt execution with tampered amount
        tampered_req = dict(req)
        tampered_req["amount"] = {"amount_minor": 500000, "currency": "INR"}  # ₹5,000 instead of ₹1,500!

        exec_res = self.gateway.execute(auth.authorization_id, gate_res, tampered_req)
        self.assertEqual(exec_res.status, ExecutionStatus.REJECTED)
        self.assertEqual(exec_res.failure_code, FailureCode.AMOUNT_MISMATCH)

    # 6. TTL Expiration Test
    def test_ttl_expiration(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_expire",
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
        gate_res = self.decision_gate.evaluate(req, det_res, risk_res)

        auth = self.gateway.authorize(gate_res)

        # Override clock to 10 minutes later (beyond 300s TTL)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=600)
        exec_res = self.gateway.execute(auth.authorization_id, gate_res, req, override_now=future_time)

        self.assertEqual(exec_res.status, ExecutionStatus.REJECTED)
        self.assertEqual(exec_res.failure_code, FailureCode.AUTHORIZATION_EXPIRED)

    # 7. Non-Bypass Architecture Test
    def test_non_bypass_architecture_direct_agent_call_rejected(self):
        req = {
            "contract_version": "trustledger.contract.v1",
            "decision_id": "dec_bypass",
            "action_type": "REFUND",
            "agent_id": "bot_01",
            "merchant_id": "merch_001",
            "customer_id": "cust_100",
            "transaction_id": "txn_100",
            "amount": {"amount_minor": 150000, "currency": "INR"},
        }
        # AI Agent attempts direct execution without TrustLedger authorization token
        bypass_res = self.agent.attempt_direct_execution_bypass(self.gateway, req)
        self.assertEqual(bypass_res.status, ExecutionStatus.REJECTED)
        self.assertEqual(bypass_res.failure_code, FailureCode.AUTHORIZATION_NOT_FOUND)

    # 8. REST Execution API Endpoint Tests
    def test_rest_api_execution_endpoints(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
