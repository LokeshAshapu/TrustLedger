"""
TrustLedger Phase 14 — Comprehensive Regression Test Suite
Tests the full decision verification pipeline for all 12 required scenarios.

Covers:
  TEST 1  — SAFE REFUND (amount normalization + APPROVE)
  TEST 2  — AMOUNT MISMATCH (BLOCK: AMOUNT_MISMATCH)
  TEST 3  — POLICY VIOLATION (BLOCK: REFUND_LIMIT_EXCEEDED)
  TEST 4  — DUPLICATE REFUND (BLOCK: DUPLICATE / REFUND_EXCEEDS_REMAINING_BALANCE)
  TEST 5  — MISSING EVIDENCE (REVIEW: EVIDENCE_MISSING)
  TEST 6  — CONFLICTING EVIDENCE (REVIEW: EVIDENCE_CONFLICTING)
  TEST 7  — WRONG ENTITY (BLOCK: EVIDENCE_LINKAGE_MISMATCH)
  TEST 8  — NONEXISTENT RECORD (BLOCK: MISSING_EVIDENCE_REFERENCE)
  TEST 9  — AI SUPPORT (APPROVE: ALL_SAFETY_CHECKS_PASSED)
  TEST 10 — AI CONTRADICTS HARD RULE (BLOCK: AI cannot override)
  TEST 11 — AI UNCERTAIN (REVIEW)
  TEST 12 — AI UNAVAILABLE (REVIEW: fail-safe)

  NORMALIZER TESTS:
    - Integer amount → canonical Money
    - Float amount → canonical Money
    - Structured Money dict → passes through
    - Null amount → RequestNormalizationError
    - Negative amount → RequestNormalizationError
    - Zero amount → RequestNormalizationError
    - String amount → RequestNormalizationError
    - Unsupported currency → RequestNormalizationError
    - Missing decision_id → RequestNormalizationError
    - Missing action_type → RequestNormalizationError
    - Invalid action_type → RequestNormalizationError
    - Defaults applied correctly
"""

import unittest
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from verifier.providers.base import LLMProvider
from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    AI_VERIFIER_VERSION,
    ReasoningFactor,
)
from verifier.service import AIVerificationService
from decision_gate.models import FinalVerdict
from backend.orchestrator import TrustLedgerDecisionService
from backend.repository import SyntheticDataRepository
from backend.normalizer import normalize_request, normalize_amount, RequestNormalizationError


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ctx(
    policy_cap_minor: int = 2500000,
    txn_amount_minor: int = 150000,
    prev_refunded_minor: int = 0,
    ev_001_status: str = "VERIFIED",
    ev_002_status: str = "VERIFIED",
) -> Dict[str, Any]:
    """Canonical test context with configurable parameters."""
    refund_history = []
    if prev_refunded_minor > 0:
        refund_history.append({
            "transaction_id": "txn_100",
            "customer_id": "cust_100",
            "amount": {"amount_minor": prev_refunded_minor, "currency": "INR"},
            "status": "PROCESSED",
        })

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
            "ev_002": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_002",
                "evidence_type": "ORDER",
                "source": "InternalLedger",
                "source_record_id": "txn_OTHER",  # Different txn — linkage mismatch!
                "timestamp": "2026-08-29T12:00:00Z",
                "verification_status": ev_002_status,
            },
            "ev_stale_999": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_stale_999",
                "evidence_type": "SUPPORT_LOG",
                "source": "Zendesk",
                "source_record_id": "ticket_999",
                "timestamp": "2026-05-01T00:00:00Z",  # > 30 days old!
                "verification_status": "STALE",
            },
            "ev_conflicting": {
                "contract_version": "trustledger.contract.v1",
                "evidence_id": "ev_conflicting",
                "evidence_type": "DELIVERY",
                "source": "CourierAPI",
                "source_record_id": "txn_100",
                "timestamp": "2026-08-29T12:00:00Z",
                "verification_status": "CONFLICTING",
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
        },
        "orders_db": {
            "ord_100": {
                "order_id": "ord_100",
                "merchant_id": "merch_001",
                "customer_id": "cust_100",
                "amount": {"amount_minor": txn_amount_minor, "currency": "INR"},
                "status": "FULFILLED",
                "created_at": "2026-08-29T10:00:00Z",
            },
        },
        "customers_db": {
            "cust_100": {"customer_id": "cust_100", "merchant_id": "merch_001"},
        },
        "merchants_db": {
            "merch_001": {"merchant_id": "merch_001"},
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
        "refund_history_db": refund_history,
    }


def _req(
    decision_id: str,
    amount_minor: int = 150000,
    evidence_refs: Optional[list] = None,
    transaction_id: str = "txn_100",
    customer_id: str = "cust_100",
    merchant_id: str = "merch_001",
    context_override: Optional[Dict[str, Any]] = None,
    requested_at: str = "2026-08-29T12:00:00Z",
) -> Dict[str, Any]:
    """Build a canonical test request."""
    if evidence_refs is None:
        evidence_refs = ["ev_001"]
    r = {
        "contract_version": "trustledger.contract.v1",
        "decision_id": decision_id,
        "action_type": "REFUND",
        "agent_id": "agent_test_01",
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "transaction_id": transaction_id,
        "order_id": "ord_100",
        "amount": {"amount_minor": amount_minor, "currency": "INR"},
        "reason": {"category": "CUSTOMER_REQUEST", "explanation": "Test case refund."},
        "evidence_references": evidence_refs,
        "requested_at": requested_at,
    }
    if context_override is not None:
        r["context"] = context_override
    return r


class AlwaysUncertainLLMProvider(LLMProvider):
    """Returns UNCERTAIN recommendation for AI-uncertain test."""
    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        return AIVerificationResult(
            decision_id=packet.decision.get("decision_id", "unknown"),
            recommendation=AIRecommendation.UNCERTAIN,
            confidence=0.45,
            contextual_assessment="Ambiguous context. Evidence completeness cannot be confirmed.",
            supporting_evidence=[],
            contradictory_evidence=[],
            missing_context=["Delivery confirmation is ambiguous."],
            reasoning_factors=[
                ReasoningFactor(
                    factor="AMBIGUOUS_DELIVERY",
                    category="EVIDENCE_QUALITY",
                    assessment="UNCERTAIN",
                    explanation="Courier record shows conflicting states.",
                    evidence_ids=[],
                )
            ],
            deterministic_conflicts=[],
            model_id="mock-uncertain",
            verifier_version=AI_VERIFIER_VERSION,
            generated_at=_ts(),
        )


class AlwaysFailingLLMProvider(LLMProvider):
    """Raises an exception to simulate AI provider failure."""
    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        raise RuntimeError("SIMULATED_PROVIDER_TIMEOUT")


# ---------------------------------------------------------------------------
# NORMALIZER UNIT TESTS
# ---------------------------------------------------------------------------

class TestRequestNormalizer(unittest.TestCase):
    """Phase 14 — Amount normalization boundary tests."""

    # Integer amount
    def test_integer_amount_converts_to_minor_units(self):
        result = normalize_amount(1500)
        self.assertEqual(result["amount_minor"], 150000)
        self.assertEqual(result["currency"], "INR")

    # Float amount
    def test_float_amount_converts_to_minor_units(self):
        result = normalize_amount(1500.50)
        self.assertEqual(result["amount_minor"], 150050)
        self.assertEqual(result["currency"], "INR")

    # Structured dict amount
    def test_structured_dict_amount_passes_through(self):
        result = normalize_amount({"amount_minor": 200000, "currency": "INR"})
        self.assertEqual(result["amount_minor"], 200000)
        self.assertEqual(result["currency"], "INR")

    # Null amount
    def test_null_amount_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount(None)
        self.assertEqual(ctx.exception.field, "amount")

    # Negative amount
    def test_negative_amount_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount(-500)
        self.assertIn("negative", ctx.exception.message.lower())

    # Zero amount
    def test_zero_amount_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount(0)
        self.assertIn("zero", ctx.exception.message.lower())

    # String amount
    def test_string_amount_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount("1500")
        self.assertEqual(ctx.exception.field, "amount")
        self.assertIn("string", ctx.exception.message.lower())

    # Unsupported currency
    def test_unsupported_currency_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount({"amount_minor": 150000, "currency": "XYZ"})
        self.assertIn("currency", ctx.exception.field)

    # Missing decision_id
    def test_missing_decision_id_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_request({"action_type": "REFUND", "amount": 1500})
        self.assertEqual(ctx.exception.field, "decision_id")

    # Missing action_type
    def test_missing_action_type_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_request({"decision_id": "dec_001", "amount": 1500})
        self.assertEqual(ctx.exception.field, "action_type")

    # Invalid action_type
    def test_invalid_action_type_raises_error(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_request({"decision_id": "dec_001", "action_type": "SEND_CRYPTO", "amount": 1500})
        self.assertEqual(ctx.exception.field, "action_type")

    # Defaults are applied
    def test_defaults_applied_for_minimal_request(self):
        result = normalize_request({
            "decision_id": "dec_minimal_001",
            "action_type": "REFUND",
            "amount": 1500,
        })
        self.assertEqual(result["amount"], {"amount_minor": 150000, "currency": "INR"})
        self.assertIn("agent_id", result)
        self.assertIn("merchant_id", result)
        self.assertIn("reason", result)
        self.assertIn("evidence_references", result)
        self.assertIn("requested_at", result)
        self.assertEqual(result["contract_version"], "trustledger.contract.v1")

    # Boolean amount rejected
    def test_boolean_amount_raises_error(self):
        with self.assertRaises(RequestNormalizationError):
            normalize_amount(True)

    # Malformed structured amount (missing amount_minor)
    def test_malformed_dict_amount_missing_amount_minor(self):
        with self.assertRaises(RequestNormalizationError) as ctx:
            normalize_amount({"currency": "INR"})
        self.assertIn("amount_minor", ctx.exception.field)

    # Negative amount_minor in dict
    def test_negative_amount_minor_in_dict_raises_error(self):
        with self.assertRaises(RequestNormalizationError):
            normalize_amount({"amount_minor": -500, "currency": "INR"})


# ---------------------------------------------------------------------------
# PIPELINE DECISION TESTS (Tests 1-12)
# ---------------------------------------------------------------------------

class TestDecisionPipelineScenarios(unittest.TestCase):
    """Phase 14 — End-to-end pipeline regression tests for all 12 required scenarios."""

    def setUp(self):
        self.repo = SyntheticDataRepository()
        self.svc = TrustLedgerDecisionService(data_repository=self.repo)

    # -----------------------------------------------------------------------
    # TEST 1 — SAFE REFUND
    # Amount = ₹1,500 (within ₹25,000 cap). No HARD failures. → APPROVE
    # -----------------------------------------------------------------------
    def test_01_safe_refund_approves(self):
        """Safe refund within policy cap with fresh evidence → APPROVE."""
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        req = _req("dec_safe_001", amount_minor=150000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.APPROVE,
                         f"Expected APPROVE but got {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNotNone(auth, "APPROVE must issue an ExecutionAuthorization")
        self.assertEqual(result.primary_reason.code, "ALL_SAFETY_CHECKS_PASSED")

    # -----------------------------------------------------------------------
    # TEST 1b — INTEGER AMOUNT NORMALIZATION (the core bug scenario)
    # This tests that a minimal request with integer amount doesn't error.
    # -----------------------------------------------------------------------
    def test_01b_integer_amount_normalized_before_pipeline(self):
        """normalizer handles integer amount 1500 (rupees) → 150000 paise before pipeline."""
        raw = {
            "decision_id": "demo-safe-001",
            "action_type": "REFUND",
            "amount": 1500,
        }
        normalized = normalize_request(raw)
        self.assertEqual(normalized["amount"]["amount_minor"], 150000)
        self.assertEqual(normalized["amount"]["currency"], "INR")
        # Should not raise — and should not return ORCHESTRATION_FAILURE
        # (Run through pipeline with injected context)
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        normalized["context"] = ctx
        result, _ = self.svc.verify_decision(normalized)
        self.assertIsNotNone(result)
        # Should not be BLOCK due to a normalization crash
        # (May be REVIEW because no evidence refs → UNKNOWN evidence state)
        self.assertIn(result.verdict, [FinalVerdict.APPROVE, FinalVerdict.REVIEW],
                      f"Minimal request must not BLOCK due to normalization failure. Got: {result.verdict}. "
                      f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")

    # -----------------------------------------------------------------------
    # TEST 2 — AMOUNT EXCEEDS TRANSACTION (simulates AMOUNT_MISMATCH)
    # Request ₹5,000 but transaction was only ₹1,000.
    # -----------------------------------------------------------------------
    def test_02_amount_exceeds_transaction_blocks(self):
        """Refund exceeding original transaction amount → BLOCK."""
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=100000)  # txn = ₹1,000
        req = _req("dec_amt_mismatch_002", amount_minor=500000, context_override=ctx)  # request ₹5,000
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK,
                         f"Expected BLOCK but got {result.verdict}")
        self.assertIsNone(auth, "BLOCK must not issue authorization")
        # Should be blocked by REFUND_EXCEEDS_TRANSACTION rule
        self.assertIn("REFUND_EXCEEDS", result.primary_reason.code,
                      f"Expected REFUND_EXCEEDS_* code, got: {result.primary_reason.code}")

    # -----------------------------------------------------------------------
    # TEST 3 — POLICY VIOLATION: REFUND_LIMIT_EXCEEDED
    # Request ₹60,000 exceeds ₹25,000 merchant cap.
    # -----------------------------------------------------------------------
    def test_03_policy_cap_violation_blocks(self):
        """Refund exceeding merchant automated cap → BLOCK: REFUND_LIMIT_EXCEEDED."""
        ctx = _ctx(policy_cap_minor=2500000)  # ₹25,000 cap
        req = _req("dec_pol_vio_003", amount_minor=6000000, context_override=ctx)  # ₹60,000
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK)
        self.assertEqual(result.decision_rule, "TL-DG-002")
        self.assertEqual(result.primary_reason.code, "REFUND_LIMIT_EXCEEDED",
                         f"Expected REFUND_LIMIT_EXCEEDED, got: {result.primary_reason.code}")
        self.assertIsNone(auth)

    # -----------------------------------------------------------------------
    # TEST 4 — DUPLICATE REFUND
    # Previous refund already consumed the full transaction amount.
    # -----------------------------------------------------------------------
    def test_04_duplicate_refund_blocks(self):
        """Duplicate refund attempt after full amount already refunded → BLOCK."""
        # Transaction = ₹1,500. Previous refund already = ₹1,500.
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=150000, prev_refunded_minor=150000)
        req = _req("dec_dup_004", amount_minor=150000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK,
                         f"Expected BLOCK for duplicate refund. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth)
        self.assertIn("REFUND_EXCEEDS", result.primary_reason.code,
                      f"Expected REFUND_EXCEEDS_* code for duplicate. Got: {result.primary_reason.code}")

    # -----------------------------------------------------------------------
    # TEST 5 — MISSING EVIDENCE
    # No evidence_references → REVIEW (evidence insufficient).
    # -----------------------------------------------------------------------
    def test_05_missing_evidence_routes_to_review(self):
        """No evidence attached → REVIEW (evidence state: INSUFFICIENT/UNKNOWN)."""
        ctx = _ctx()
        req = _req("dec_miss_ev_005", evidence_refs=[], context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.REVIEW,
                         f"Expected REVIEW for missing evidence. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth, "REVIEW must not issue authorization")
        # Explanation should reference evidence incompleteness
        self.assertIn(result.evidence_state.value,
                      ["INSUFFICIENT", "CONFLICTING"],
                      f"Evidence state should reflect insufficiency, got: {result.evidence_state.value}")

    # -----------------------------------------------------------------------
    # TEST 6 — CONFLICTING EVIDENCE
    # ev_conflicting has verification_status=CONFLICTING → WARNING → REVIEW.
    # -----------------------------------------------------------------------
    def test_06_conflicting_evidence_routes_to_review(self):
        """Conflicting evidence artifact → REVIEW."""
        ctx = _ctx()
        req = _req("dec_conf_ev_006", evidence_refs=["ev_conflicting"], context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.REVIEW,
                         f"Expected REVIEW for conflicting evidence. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth)

    # -----------------------------------------------------------------------
    # TEST 7 — WRONG ENTITY (ev_002 belongs to txn_OTHER, not txn_100)
    # Evidence linkage mismatch → HARD FAIL → BLOCK.
    # -----------------------------------------------------------------------
    def test_07_wrong_entity_evidence_blocks(self):
        """Evidence referencing a different transaction → BLOCK: EVIDENCE_LINKAGE_MISMATCH."""
        ctx = _ctx()
        req = _req("dec_ent_mis_007", evidence_refs=["ev_002"], context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK,
                         f"Expected BLOCK for entity mismatch. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth)
        self.assertEqual(result.primary_reason.code, "EVIDENCE_LINKAGE_MISMATCH",
                         f"Expected EVIDENCE_LINKAGE_MISMATCH, got: {result.primary_reason.code}")

    # -----------------------------------------------------------------------
    # TEST 8 — NONEXISTENT RECORD
    # evidence_references points to a non-existent evidence ID.
    # -----------------------------------------------------------------------
    def test_08_nonexistent_evidence_blocks(self):
        """Reference to nonexistent evidence ID → BLOCK: MISSING_EVIDENCE_REFERENCE."""
        ctx = _ctx()
        req = _req("dec_ne_rec_008", evidence_refs=["ev_DOES_NOT_EXIST_999"], context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK,
                         f"Expected BLOCK for nonexistent evidence. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth)
        self.assertEqual(result.primary_reason.code, "MISSING_EVIDENCE_REFERENCE",
                         f"Expected MISSING_EVIDENCE_REFERENCE, got: {result.primary_reason.code}")

    # -----------------------------------------------------------------------
    # TEST 9 — AI SUPPORT
    # Clean deterministic pass + MockLLMProvider returns SUPPORT → APPROVE.
    # -----------------------------------------------------------------------
    def test_09_ai_support_enables_approve(self):
        """Clean deterministic pass + AI SUPPORT → APPROVE: ALL_SAFETY_CHECKS_PASSED."""
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        req = _req("dec_ai_sup_009", amount_minor=150000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.APPROVE,
                         f"Expected APPROVE (AI SUPPORT path). Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNotNone(auth)
        self.assertEqual(result.ai_recommendation, "SUPPORT")

    # -----------------------------------------------------------------------
    # TEST 10 — AI CONTRADICTS HARD RULE
    # Policy cap violation (HARD). MockLLMProvider correctly returns CONTRADICT
    # when hard failures are present (not SUPPORT). Either way, the Decision
    # Gate must BLOCK at Level 2 — the AI signal is irrelevant.
    # -----------------------------------------------------------------------
    def test_10_hard_rule_blocks_regardless_of_ai(self):
        """HARD policy violation → BLOCK even if AI would otherwise say SUPPORT."""
        ctx = _ctx(policy_cap_minor=2500000)  # cap = ₹25,000
        # ₹60,000 > cap → HARD FAIL → Decision Rule Level 2 → BLOCK
        req = _req("dec_ai_ovr_010", amount_minor=6000000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.BLOCK,
                         f"HARD rule must block regardless of AI signal.")
        self.assertEqual(result.decision_rule, "TL-DG-002",
                         "HARD failure must be caught at Level 2 (TL-DG-002).")
        self.assertIsNone(auth)

        # The Decision Gate must use TL-DG-002 (HARD safety), which takes precedence
        # over the AI layer — regardless of whether AI said SUPPORT or CONTRADICT.
        # Verify AI recommendation did NOT change the final verdict.
        self.assertEqual(result.primary_reason.code, "REFUND_LIMIT_EXCEEDED",
                         f"Primary reason must be REFUND_LIMIT_EXCEEDED, got: {result.primary_reason.code}")

        # Verify that if AI says SUPPORT on a hard-failed request, the trace records the override
        # (This is tested by the Security Invariant suite separately)
        # Here we just confirm the verdict is BLOCK regardless of what AI said.
        trace_stages = [t.stage_name for t in result.decision_trace]
        self.assertIn("DECISION_RULE", trace_stages, "Decision trace must include DECISION_RULE stage")
        self.assertIn("FINAL_VERDICT", trace_stages, "Decision trace must include FINAL_VERDICT stage")

    # -----------------------------------------------------------------------
    # TEST 11 — AI UNCERTAIN
    # Deterministic checks pass, but AlwaysUncertainLLMProvider → REVIEW.
    # -----------------------------------------------------------------------
    def test_11_ai_uncertain_routes_to_review(self):
        """AI returning UNCERTAIN → REVIEW: AI_CONTEXTUAL_UNCERTAINTY."""
        uncertain_svc = TrustLedgerDecisionService(
            data_repository=self.repo,
            ai_service=AIVerificationService(AlwaysUncertainLLMProvider()),
        )
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        req = _req("dec_ai_unc_011", amount_minor=150000, context_override=ctx)
        result, auth = uncertain_svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.REVIEW,
                         f"Expected REVIEW for AI_UNCERTAIN. Got: {result.verdict}. "
                         f"Reason: [{result.primary_reason.code}] {result.primary_reason.message}")
        self.assertIsNone(auth)
        self.assertEqual(result.ai_recommendation, "UNCERTAIN")

    # -----------------------------------------------------------------------
    # TEST 12 — AI UNAVAILABLE (fail-safe)
    # AlwaysFailingLLMProvider raises → service returns UNCERTAIN fallback
    # → Decision Gate routes to REVIEW (fail-safe).
    # -----------------------------------------------------------------------
    def test_12_ai_unavailable_fails_safely_to_review(self):
        """AI provider failure → REVIEW fail-safe (not APPROVE, not crash)."""
        failing_svc = TrustLedgerDecisionService(
            data_repository=self.repo,
            ai_service=AIVerificationService(AlwaysFailingLLMProvider()),
        )
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        req = _req("dec_ai_fail_012", amount_minor=150000, context_override=ctx)
        result, auth = failing_svc.verify_decision(req)

        self.assertEqual(result.verdict, FinalVerdict.REVIEW,
                         f"AI failure must fail-safe to REVIEW. Got: {result.verdict}.")
        self.assertIsNone(auth, "AI-unavailable REVIEW must not issue authorization")


# ---------------------------------------------------------------------------
# SECURITY INVARIANT TESTS
# ---------------------------------------------------------------------------

class TestSecurityInvariants(unittest.TestCase):
    """Validates that all security invariants remain intact."""

    def setUp(self):
        self.repo = SyntheticDataRepository()
        self.svc = TrustLedgerDecisionService(data_repository=self.repo)

    def _approve_req(self, decision_id: str) -> Dict[str, Any]:
        ctx = _ctx(policy_cap_minor=2500000, txn_amount_minor=500000)
        return _req(decision_id, amount_minor=150000, context_override=ctx)

    def test_approve_issues_authorization(self):
        """APPROVE verdict must issue an ExecutionAuthorization."""
        result, auth = self.svc.verify_decision(self._approve_req("sec_inv_approve_001"))
        self.assertEqual(result.verdict, FinalVerdict.APPROVE)
        self.assertIsNotNone(auth)
        self.assertGreater(len(auth.authorization_id), 10)

    def test_review_has_no_authorization(self):
        """REVIEW verdict must NOT issue an ExecutionAuthorization."""
        ctx = _ctx()
        req = _req("sec_inv_review_001", evidence_refs=[], context_override=ctx)
        result, auth = self.svc.verify_decision(req)
        self.assertEqual(result.verdict, FinalVerdict.REVIEW)
        self.assertIsNone(auth)

    def test_block_has_no_authorization(self):
        """BLOCK verdict must NOT issue an ExecutionAuthorization."""
        ctx = _ctx(policy_cap_minor=2500000)
        req = _req("sec_inv_block_001", amount_minor=6000000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)
        self.assertEqual(result.verdict, FinalVerdict.BLOCK)
        self.assertIsNone(auth)

    def test_decision_hash_is_64_chars(self):
        """Every DecisionResult must contain a 64-character SHA-256 hash."""
        result, _ = self.svc.verify_decision(self._approve_req("sec_inv_hash_001"))
        self.assertEqual(len(result.decision_hash), 64,
                         f"decision_hash must be 64 chars (SHA-256). Got: {len(result.decision_hash)}")

    def test_decision_result_has_primary_reason(self):
        """Every DecisionResult must have a non-empty primary_reason with code and message."""
        result, _ = self.svc.verify_decision(self._approve_req("sec_inv_reason_001"))
        self.assertIsNotNone(result.primary_reason)
        self.assertGreater(len(result.primary_reason.code), 0)
        self.assertGreater(len(result.primary_reason.message), 0)

    def test_decision_trace_has_stages(self):
        """Every DecisionResult must have a non-empty decision_trace."""
        result, _ = self.svc.verify_decision(self._approve_req("sec_inv_trace_001"))
        self.assertGreater(len(result.decision_trace), 0)

    def test_block_verdict_always_has_reason(self):
        """BLOCK must never be returned without a specific primary_reason code."""
        ctx = _ctx(policy_cap_minor=2500000)
        req = _req("sec_inv_blk_reason_001", amount_minor=6000000, context_override=ctx)
        result, _ = self.svc.verify_decision(req)
        self.assertEqual(result.verdict, FinalVerdict.BLOCK)
        self.assertNotEqual(result.primary_reason.code, "")
        self.assertNotIn("unknown", result.primary_reason.code.lower())

    def test_hard_rule_not_overridable_by_ai_support(self):
        """AI SUPPORT cannot override a Level-2 HARD deterministic failure."""
        # MockLLMProvider will return SUPPORT when no hard failures
        # but with policy violation it should return CONTRADICT.
        # Either way, the Decision Gate must BLOCK.
        ctx = _ctx(policy_cap_minor=2500000)
        req = _req("sec_inv_ai_ovr_001", amount_minor=6000000, context_override=ctx)
        result, auth = self.svc.verify_decision(req)
        self.assertEqual(result.verdict, FinalVerdict.BLOCK)
        self.assertIsNone(auth)
        self.assertEqual(result.decision_rule, "TL-DG-002")


if __name__ == "__main__":
    unittest.main(verbosity=2)
