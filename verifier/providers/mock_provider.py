"""
TrustLedger Deterministic Mock LLM Provider for Testing
Phase 5 AI Contextual Verification Layer
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    ReasoningFactor,
    ContradictoryEvidenceItem,
    DeterministicConflictItem,
    AI_VERIFIER_VERSION,
)
from verifier.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM Provider for unit tests.
    Returns structured AI results without external network calls or API costs.
    """

    def __init__(self, model_id: str = "mock-llama-3.1-70b"):
        self.model_id = model_id
        self.simulate_timeout = False
        self.simulate_malformed = False
        self.simulate_invalid_evidence = False

    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        if self.simulate_timeout:
            raise TimeoutError("Mock LLM Provider timed out after 10.0 seconds")

        d_id = packet.decision.get("decision_id", "unknown")
        det_res = packet.deterministic_result
        hard_failures = det_res.get("hard_failures", [])
        warnings = det_res.get("warnings", [])
        evidence_list = packet.relevant_evidence
        valid_ev_ids = [e["evidence_id"] for e in evidence_list]

        supporting_ids = [eid for eid in valid_ev_ids if not eid.startswith("ev_failed")]
        if self.simulate_invalid_evidence:
            supporting_ids.append("ev_FAKE_NONEXISTENT_999")

        factors: List[ReasoningFactor] = []
        conflicts: List[DeterministicConflictItem] = []
        contradictory_items: List[ContradictoryEvidenceItem] = []
        missing_context: List[str] = []

        # Case 1: Hard Deterministic Violations Present -> CONTRADICT
        if hard_failures:
            rec = AIRecommendation.CONTRADICT
            conf = 0.92
            assessment = "Contextual analysis confirms hard deterministic rule violations. Proposed financial action contradicts ledger facts or policy thresholds."

            for h in hard_failures:
                code = h.get("code", "UNKNOWN_FAIL")
                msg = h.get("message", "Hard rule failure.")
                conflicts.append(
                    DeterministicConflictItem(
                        finding_code=code,
                        acknowledged=True,
                        explanation=f"Acknowledged HARD deterministic violation: {msg}",
                    )
                )

            for ev in evidence_list:
                if ev.get("verification_status") in ["FAILED", "CONFLICTING"]:
                    contradictory_items.append(
                        ContradictoryEvidenceItem(
                            evidence_id=ev.get("evidence_id", "ev_unknown"),
                            issue=f"Evidence artifact status is {ev.get('verification_status')}.",
                            impact="CONTRADICTS",
                        )
                    )

            factors.append(
                ReasoningFactor(
                    factor="DETERMINISTIC_HARD_SAFETY_VIOLATION",
                    category="POLICY_AND_CONSISTENCY",
                    assessment="CONTRADICTS",
                    explanation="Transaction payload violates hard merchant policy cap or entity relationship.",
                    evidence_ids=valid_ev_ids[:2],
                )
            )

        # Case 2: Evidence Uncertainty / Warnings Present -> UNCERTAIN
        elif warnings:
            rec = AIRecommendation.UNCERTAIN
            conf = 0.65
            assessment = "Contextual analysis indicates ambiguous or incomplete evidence. Human verification is advised."
            missing_context.append("Independent courier delivery confirmation or proof of return receipt.")

            for w in warnings:
                code = w.get("code", "WARNING_CODE")
                if "MISSING" in code or "NO_EVIDENCE" in code:
                    missing_context.append(f"Missing evidence artifact for rule check '{code}'.")

            factors.append(
                ReasoningFactor(
                    factor="EVIDENCE_INCOMPLETENESS",
                    category="EVIDENCE_QUALITY",
                    assessment="UNCERTAIN",
                    explanation="Attached evidence records contain status flags or missing provenance.",
                    evidence_ids=valid_ev_ids[:1],
                )
            )

        # Case 3: Clean Pass -> SUPPORT
        else:
            rec = AIRecommendation.SUPPORT
            conf = 0.95
            assessment = "Contextual evidence, historical activity, and transaction parameters fully support the proposed financial decision."
            factors.append(
                ReasoningFactor(
                    factor="VALID_HISTORICAL_ALIGNMENT",
                    category="TRANSACTION_CONTEXT",
                    assessment="SUPPORTS",
                    explanation="Order, delivery receipt, and customer payment history form a consistent narrative.",
                    evidence_ids=supporting_ids[:2],
                )
            )

        return AIVerificationResult(
            decision_id=d_id,
            recommendation=rec,
            confidence=conf,
            contextual_assessment=assessment,
            supporting_evidence=supporting_ids,
            contradictory_evidence=contradictory_items,
            missing_context=missing_context,
            reasoning_factors=factors,
            deterministic_conflicts=conflicts,
            model_id=self.model_id,
            verifier_version=AI_VERIFIER_VERSION,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
