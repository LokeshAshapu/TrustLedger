"""
TrustLedger Deterministic Decision Matrix Rules (TL-DG-001 to TL-DG-011)
Phase 6 Signal Aggregation & Decision Layer
"""

from typing import Dict, Any, List, Tuple, Optional
from decision_gate.models import FinalVerdict, EvidenceQualityState, PrimaryReason


class DecisionRuleEngine:
    """
    Evaluates explicit, auditable decision rules with strict precedence.
    Hierarchy:
      Level 1: Contract Safety -> BLOCK
      Level 2: Hard Deterministic Safety -> BLOCK (AI CANNOT OVERRIDE THIS)
      Level 3: Execution Risk -> REVIEW
      Level 4: Evidence Uncertainty -> REVIEW
      Level 5: AI Contextual Reasoning -> REVIEW / APPROVE
    """

    @staticmethod
    def evaluate(
        request: Dict[str, Any],
        det_result: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        ai_result: Optional[Dict[str, Any]],
    ) -> Tuple[FinalVerdict, str, PrimaryReason, EvidenceQualityState, List[str]]:

        contributing_findings: List[str] = []

        # ---------------------------------------------------------------------
        # 0. Determine Evidence Quality State
        # ---------------------------------------------------------------------
        warnings = det_result.get("warnings", [])
        evidence_state = EvidenceQualityState.SUFFICIENT

        for w in warnings:
            w_code = w.get("code", "")
            contributing_findings.append(w_code)
            if "CONFLICT" in w_code:
                evidence_state = EvidenceQualityState.CONFLICTING
            elif "MISSING" in w_code or "NO_EVIDENCE" in w_code or "STALE" in w_code:
                if evidence_state != EvidenceQualityState.CONFLICTING:
                    evidence_state = EvidenceQualityState.INSUFFICIENT


        hard_failures = det_result.get("hard_failures", [])
        for h in hard_failures:
            contributing_findings.append(h.get("code", "HARD_FAILURE"))

        # ---------------------------------------------------------------------
        # LEVEL 1 — CONTRACT SAFETY CHECK
        # ---------------------------------------------------------------------
        if not request.get("decision_id") or not request.get("action_type") or not request.get("amount"):
            return (
                FinalVerdict.BLOCK,
                "TL-DG-001",
                PrimaryReason(code="CONTRACT_INVALID", message="Malformed or contractually invalid decision request."),
                evidence_state,
                contributing_findings,
            )

        # ---------------------------------------------------------------------
        # LEVEL 2 — HARD DETERMINISTIC SAFETY CHECK (AI CANNOT OVERRIDE THIS!)
        # ---------------------------------------------------------------------
        if hard_failures:
            primary_hard = hard_failures[0]
            p_code = primary_hard.get("code", "HARD_SAFETY_VIOLATION")
            p_msg = primary_hard.get("message", "Hard deterministic safety policy violation.")
            return (
                FinalVerdict.BLOCK,
                "TL-DG-002",
                PrimaryReason(code=p_code, message=p_msg),
                evidence_state,
                contributing_findings,
            )

        # ---------------------------------------------------------------------
        # LEVEL 4 — EVIDENCE UNCERTAINTY CHECKS
        # ---------------------------------------------------------------------
        if evidence_state == EvidenceQualityState.INSUFFICIENT:
            return (
                FinalVerdict.REVIEW,
                "TL-DG-003",
                PrimaryReason(code="EVIDENCE_MISSING", message="Critical evidence artifact missing or unverified."),
                evidence_state,
                contributing_findings,
            )

        if evidence_state == EvidenceQualityState.CONFLICTING:
            return (
                FinalVerdict.REVIEW,
                "TL-DG-004",
                PrimaryReason(code="EVIDENCE_CONFLICTING", message="Conflicting evidence artifacts detected across source ledgers."),
                evidence_state,
                contributing_findings,
            )

        # ---------------------------------------------------------------------
        # LEVEL 3 — EXECUTION RISK CHECKS
        # ---------------------------------------------------------------------
        risk_level = risk_assessment.get("risk_level", "LOW")
        risk_score = risk_assessment.get("risk_score", 0.0)

        if risk_level == "CRITICAL" or risk_score >= 0.75:
            return (
                FinalVerdict.REVIEW,
                "TL-DG-005",
                PrimaryReason(code="CRITICAL_FINANCIAL_RISK", message="Proposed financial action carries CRITICAL exposure risk."),
                evidence_state,
                contributing_findings,
            )

        if risk_level == "HIGH" or risk_score >= 0.50:
            return (
                FinalVerdict.REVIEW,
                "TL-DG-006",
                PrimaryReason(code="HIGH_FINANCIAL_RISK", message="Proposed financial action carries HIGH exposure risk."),
                evidence_state,
                contributing_findings,
            )

        # ---------------------------------------------------------------------
        # LEVEL 5 — AI CONTEXTUAL REASONING CHECKS
        # ---------------------------------------------------------------------
        if ai_result:
            ai_rec = ai_result.get("recommendation", "UNCERTAIN")

            if ai_rec == "CONTRADICT":
                return (
                    FinalVerdict.REVIEW,
                    "TL-DG-007",
                    PrimaryReason(code="AI_CONTEXTUAL_CONTRADICTION", message="Contextual AI verification flagged contradictory narrative or evidence."),
                    evidence_state,
                    contributing_findings,
                )

            if ai_rec == "UNCERTAIN":
                return (
                    FinalVerdict.REVIEW,
                    "TL-DG-008",
                    PrimaryReason(code="AI_CONTEXTUAL_UNCERTAINTY", message="Contextual AI verification indicates ambiguous or incomplete context."),
                    evidence_state,
                    contributing_findings,
                )

            if ai_rec == "AI_UNAVAILABLE":
                return (
                    FinalVerdict.REVIEW,
                    "TL-DG-009",
                    PrimaryReason(code="AI_VERIFIER_UNAVAILABLE", message="AI contextual verifier service unavailable; routing to manual review."),
                    evidence_state,
                    contributing_findings,
                )

            if ai_rec == "SUPPORT" and risk_level in ["LOW", "MEDIUM"] and evidence_state == EvidenceQualityState.SUFFICIENT:
                return (
                    FinalVerdict.APPROVE,
                    "TL-DG-010",
                    PrimaryReason(code="ALL_SAFETY_CHECKS_PASSED", message="All contract, policy, consistency, risk, and contextual checks passed."),
                    evidence_state,
                    contributing_findings,
                )

        # Clean Pass without AI execution (Optional AI skipped for bounded Low Risk)
        if risk_level == "LOW" and evidence_state == EvidenceQualityState.SUFFICIENT:
            return (
                FinalVerdict.APPROVE,
                "TL-DG-011",
                PrimaryReason(code="LOW_RISK_CLEAN_PASS", message="Bounded low-risk financial action passed all deterministic safety rules."),
                evidence_state,
                contributing_findings,
            )

        # Default Safety Fallback -> REVIEW
        return (
            FinalVerdict.REVIEW,
            "TL-DG-008",
            PrimaryReason(code="DEFAULT_SAFETY_REVIEW", message="Decision context requires human verification."),
            evidence_state,
            contributing_findings,
        )
