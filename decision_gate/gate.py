"""
TrustLedger Master Signal Aggregation Decision Gate
Phase 6 Signal Aggregation & Decision Layer
Gate Version: trustledger.decision-gate.v1
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from verifier.deterministic.models import DeterministicVerificationResult
from risk_engine.models import RiskAssessment
from verifier.ai_models import AIVerificationResult

from decision_gate.models import (
    DecisionResult,
    FinalVerdict,
    EvidenceQualityState,
    PrimaryReason,
    StageTrace,
    GATE_VERSION,
)
from decision_gate.rules import DecisionRuleEngine
from decision_gate.review_builder import ReviewContextBuilder
from decision_gate.hashing import compute_decision_hash


class DecisionGate:
    """
    Master Decision Gate.
    Authoritative, 100% deterministic decision layer that combines contract validation,
    deterministic verification findings, risk assessments, and AI contextual verifier outputs
    into an auditable DecisionResult (APPROVE, REVIEW, BLOCK).
    """

    def __init__(self):
        self.version = GATE_VERSION

    def evaluate(
        self,
        request: Dict[str, Any],
        det_result: DeterministicVerificationResult,
        risk_assessment: RiskAssessment,
        ai_result: Optional[AIVerificationResult] = None,
    ) -> DecisionResult:

        d_id = request.get("decision_id", "unknown_decision")
        now_iso = datetime.now(timezone.utc).isoformat()
        trace: List[StageTrace] = []

        det_dict = det_result.model_dump()
        risk_dict = risk_assessment.model_dump()
        ai_dict = ai_result.model_dump() if ai_result else None

        # ---------------------------------------------------------------------
        # Stage 1: Contract Validation Trace
        # ---------------------------------------------------------------------
        valid_contract = bool(request.get("decision_id") and request.get("action_type") and request.get("amount"))
        trace.append(
            StageTrace(
                stage_name="CONTRACT",
                status="PASS" if valid_contract else "FAIL",
                input_summary=f"Action: {request.get('action_type')}, Amount: {request.get('amount')}",
                output_summary="Canonical DecisionRequest payload format valid." if valid_contract else "Contract invalid.",
                timestamp=now_iso,
            )
        )

        # ---------------------------------------------------------------------
        # Stage 2: Deterministic Checks Trace
        # ---------------------------------------------------------------------
        hard_count = len(det_result.hard_failures)
        warn_count = len(det_result.warnings)
        trace.append(
            StageTrace(
                stage_name="DETERMINISTIC_CHECKS",
                status="FAIL" if hard_count > 0 else ("WARNING" if warn_count > 0 else "PASS"),
                input_summary=f"Evidence checks executed across policy & ledger.",
                output_summary=f"HARD Failures: {hard_count}, Warnings: {warn_count}",
                timestamp=now_iso,
            )
        )

        # ---------------------------------------------------------------------
        # Stage 3: Risk Assessment Trace
        # ---------------------------------------------------------------------
        trace.append(
            StageTrace(
                stage_name="RISK_ASSESSMENT",
                status=risk_assessment.risk_level.value,
                input_summary=f"Gross Exposure: {risk_assessment.exposure.gross_exposure.amount_minor} paise",
                output_summary=f"Risk Score: {risk_assessment.risk_score:.4f}, Level: {risk_assessment.risk_level.value}",
                timestamp=now_iso,
            )
        )

        # ---------------------------------------------------------------------
        # Stage 4: AI Context Trace
        # ---------------------------------------------------------------------
        ai_rec_str = ai_result.recommendation.value if ai_result else "SKIPPED"
        trace.append(
            StageTrace(
                stage_name="AI_CONTEXT",
                status=ai_rec_str,
                input_summary=f"Model: {ai_result.model_id if ai_result else 'N/A'}",
                output_summary=f"AI Recommendation: {ai_rec_str}, Confidence: {ai_result.confidence if ai_result else 0.0:.2f}",
                timestamp=now_iso,
            )
        )

        # Audit Check: Record AI Disagreement Trace if AI SUPPORT tried to override HARD failure
        if hard_count > 0 and ai_result and ai_result.recommendation.value == "SUPPORT":
            trace.append(
                StageTrace(
                    stage_name="AI_DISAGREEMENT_OVERRIDE",
                    status="AI_OVERRIDDEN",
                    input_summary=f"AI Recommendation: SUPPORT (Confidence: {ai_result.confidence:.2f})",
                    output_summary="AI_SUPPORT_DID_NOT_OVERRIDE_HARD_DETERMINISTIC_RULE: AI recommendation 'SUPPORT' was explicitly overridden by HARD deterministic safety rule.",
                    rule_id="TL-DG-002",
                    timestamp=now_iso,
                )
            )

        # ---------------------------------------------------------------------
        # Stage 5: Decision Matrix Evaluation
        # ---------------------------------------------------------------------
        verdict, rule_id, primary_reason, evidence_state, findings = DecisionRuleEngine.evaluate(
            request, det_dict, risk_dict, ai_dict
        )

        trace.append(
            StageTrace(
                stage_name="DECISION_RULE",
                status=verdict.value,
                input_summary=f"Deterministic failures: {hard_count}, Risk: {risk_assessment.risk_level.value}, AI: {ai_rec_str}",
                output_summary=f"Matched Rule: {rule_id} ({primary_reason.code})",
                rule_id=rule_id,
                timestamp=now_iso,
            )
        )

        trace.append(
            StageTrace(
                stage_name="FINAL_VERDICT",
                status=verdict.value,
                input_summary=f"Primary Reason: [{primary_reason.code}] {primary_reason.message}",
                output_summary=f"Final Decision Gate Verdict: {verdict.value}",
                rule_id=rule_id,
                timestamp=now_iso,
            )
        )

        # Build ReviewContext for REVIEW decisions
        review_ctx = None
        if verdict == FinalVerdict.REVIEW:
            review_ctx = ReviewContextBuilder.build(
                d_id, request, det_dict, risk_dict, ai_dict, evidence_state.value
            )

        # Construct Preliminary Decision Result Payload
        result_dict = {
            "decision_id": d_id,
            "verdict": verdict.value,
            "decision_rule": rule_id,
            "primary_reason": primary_reason.model_dump(),
            "contributing_findings": findings,
            "risk_level": risk_assessment.risk_level.value,
            "risk_score": risk_assessment.risk_score,
            "ai_recommendation": ai_rec_str,
            "evidence_state": evidence_state.value,
            "review_context": review_ctx.model_dump() if review_ctx else None,
            "decision_trace": [t.model_dump() for t in trace],
            "gate_version": self.version,
            "decided_at": now_iso,
        }

        # Compute Cryptographic SHA-256 Hash Over Canonical Payload
        d_hash = compute_decision_hash(result_dict)
        result_dict["decision_hash"] = d_hash

        return DecisionResult.model_validate(result_dict)
