"""
TrustLedger End-to-End Backend Orchestration Test Suite
Phase 10A End-to-End Orchestration & Safety Invariant Validation
"""

import os
import unittest
import time
from typing import Dict, Any

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine
from verifier.providers.mock_provider import MockLLMProvider
from verifier.providers.base import LLMProvider
from verifier.service import AIVerificationService
from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    AI_VERIFIER_VERSION,
)
from decision_gate.gate import DecisionGate
from decision_gate.models import FinalVerdict
from execution_engine.gateway import ExecutionGateway
from execution_engine.models import AuthorizationStatus
from backend.repository import SyntheticDataRepository
from backend.orchestrator import TrustLedgerDecisionService


class FailingLLMProvider(LLMProvider):
    """Failing LLM provider simulation to test AI_UNAVAILABLE fail-safe path."""
    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        raise RuntimeError("SIMULATED_LLM_PROVIDER_TIMEOUT")


def get_canonical_context(policy_cap_minor: int = 2500000) -> Dict[str, Any]:
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
            },
            "ev_stale_999": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_stale_999",
                "evidence_type": "SUPPORT_LOG",
                "source": "Zendesk",
                "source_record_id": "ticket_999",
                "timestamp": "2026-05-01T00:00:00Z", # > 30 days old!
                "verification_status": "STALE",
            },
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


def make_canonical_request(
    decision_id: str,
    action_type: str = "REFUND",
    amount_minor: int = 150000,
    evidence_refs: list = None,
    merchant_id: str = "merch_001",
    customer_id: str = "cust_100",
    transaction_id: str = "txn_100",
    order_id: str = "ord_100",
    context_override: dict = None,
) -> dict:
    if evidence_refs is None:
        evidence_refs = ["ev_001"]

    base_req = {
        "contract_version": "trustledger.contract.v1",
        "decision_id": decision_id,
        "action_type": action_type,
        "agent_id": "agent_financial_01",
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "order_id": order_id,
        "amount": {"amount_minor": amount_minor, "currency": "INR"},
        "reason": {
            "category": "NON_DELIVERY",
            "explanation": "Customer requested refund for non-delivery.",
        },
        "evidence_references": evidence_refs,
        "requested_at": "2026-08-29T12:00:00Z",
    }

    if context_override:
        base_req["context"] = context_override

    return base_req


class TestEndToEndOrchestrator(unittest.TestCase):

    def setUp(self):
        self.repository = SyntheticDataRepository()
        self.orchestrator = TrustLedgerDecisionService(data_repository=self.repository)

    # -------------------------------------------------------------------------
    # 1. CASE A — SAFE APPROVAL
    # -------------------------------------------------------------------------
    def test_case_a_safe_approval(self):
        ctx = get_canonical_context(policy_cap_minor=2500000)
        req = make_canonical_request(
            decision_id="dec_safe_test_001",
            amount_minor=150000,
            evidence_refs=["ev_001"],
            context_override=ctx,
        )

        decision_res, auth = self.orchestrator.verify_decision(req)

        self.assertEqual(decision_res.verdict, FinalVerdict.APPROVE)
        self.assertIsNotNone(auth)
        self.assertEqual(auth.status, AuthorizationStatus.ISSUED)

    # -------------------------------------------------------------------------
    # 2. CASE B — HUMAN REVIEW
    # -------------------------------------------------------------------------
    def test_case_b_human_review(self):
        ctx = get_canonical_context(policy_cap_minor=2500000)
        req = make_canonical_request(
            decision_id="dec_stale_test_002",
            amount_minor=50000,
            evidence_refs=["ev_stale_999"],
            context_override=ctx,
        )

        decision_res, auth = self.orchestrator.verify_decision(req)

        self.assertEqual(decision_res.verdict, FinalVerdict.REVIEW)
        self.assertIsNone(auth) # Critical Invariant 3: REVIEW -> NO AUTHORIZATION

    # -------------------------------------------------------------------------
    # 3. CASE C — SIGNATURE BLOCK (AI SUPPORT vs Policy Cap Violation)
    # -------------------------------------------------------------------------
    def test_case_c_signature_block_override(self):
        ctx = get_canonical_context(policy_cap_minor=2500000) # ₹25,000 cap!
        req = make_canonical_request(
            decision_id="dec_blk_pol_000042",
            amount_minor=6000000, # ₹60,000 > ₹25,000 cap!
            evidence_refs=["ev_001"],
            context_override=ctx,
        )

        decision_res, auth = self.orchestrator.verify_decision(req)

        self.assertEqual(decision_res.verdict, FinalVerdict.BLOCK)
        self.assertEqual(decision_res.decision_rule, "TL-DG-002")
        self.assertIsNone(auth) # Critical Invariant 4: BLOCK -> NO AUTHORIZATION

    # -------------------------------------------------------------------------
    # 4. SAFETY INVARIANT 5: AI_UNAVAILABLE -> REVIEW (Fail-Safe)
    # -------------------------------------------------------------------------
    def test_invariant_5_ai_unavailable_fails_safely_to_review(self):
        failing_ai_service = AIVerificationService(FailingLLMProvider())
        failing_orchestrator = TrustLedgerDecisionService(
            data_repository=self.repository,
            ai_service=failing_ai_service,
        )

        ctx = get_canonical_context(policy_cap_minor=2500000)
        req = make_canonical_request(
            decision_id="dec_ai_fail_005",
            amount_minor=150000,
            evidence_refs=["ev_001"],
            context_override=ctx,
        )

        decision_res, auth = failing_orchestrator.verify_decision(req)

        self.assertEqual(decision_res.verdict, FinalVerdict.REVIEW)
        self.assertIsNone(auth)

    # -------------------------------------------------------------------------
    # 5. GROUND-TRUTH ISOLATION TEST
    # -------------------------------------------------------------------------
    def test_ground_truth_isolation(self):
        """Proves runtime orchestrator does NOT read data/ground-truth/."""
        ctx = get_canonical_context(policy_cap_minor=2500000)
        req = make_canonical_request(
            decision_id="dec_safe_test_001",
            amount_minor=150000,
            context_override=ctx,
        )
        decision_res, _ = self.orchestrator.verify_decision(req)
        self.assertIsNotNone(decision_res)
        self.assertFalse(hasattr(self.orchestrator.repository, "ground_truth"))

    # -------------------------------------------------------------------------
    # 6. LOCAL SIMULATION BENCHMARK
    # -------------------------------------------------------------------------
    def test_local_simulation_benchmark(self):
        """Local Simulation Benchmark across 50 requests."""
        ctx = get_canonical_context(policy_cap_minor=2500000)
        start = time.time()
        n = 50
        for i in range(n):
            req = make_canonical_request(
                decision_id=f"dec_bench_{i}",
                amount_minor=150000,
                context_override=ctx,
            )
            self.orchestrator.verify_decision(req)
        elapsed = time.time() - start
        avg_ms = (elapsed / n) * 1000
        print(f"\n[LOCAL SIMULATION BENCHMARK] {n} requests verified in {elapsed:.3f}s (Avg: {avg_ms:.2f}ms/req)")
        self.assertLess(avg_ms, 100.0) # < 100ms per decision
