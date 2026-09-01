"""
TrustLedger ReviewContext & Question Generator
Phase 6 Signal Aggregation & Decision Layer
"""

from typing import Dict, Any, List, Optional
from decision_gate.models import ReviewContext, ReviewerQuestion


class ReviewContextBuilder:
    """
    Constructs a structured ReviewContext containing targeted, deterministic reviewer questions
    for cases routed to human review (FinalVerdict.REVIEW).
    """

    @staticmethod
    def build(
        decision_id: str,
        request: Dict[str, Any],
        det_result: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        ai_result: Optional[Dict[str, Any]],
        evidence_state: str,
    ) -> ReviewContext:
        action_type = request.get("action_type", "UNKNOWN_ACTION")
        amount_dict = request.get("amount", {})
        gross_inr = amount_dict.get("amount_minor", 0) / 100.0

        risk_level = risk_assessment.get("risk_level", "UNKNOWN")
        risk_score = risk_assessment.get("risk_score", 0.0)

        det_findings = [f.get("message", "") for f in det_result.get("warnings", [])]
        for h in det_result.get("hard_failures", []):
            det_findings.append(f"[HARD FAILURE] {h.get('message', '')}")

        ai_summary = ai_result.get("contextual_assessment") if ai_result else "AI Verification not executed."
        supporting_ids = ai_result.get("supporting_evidence", []) if ai_result else []
        contradictory_items = ai_result.get("contradictory_evidence", []) if ai_result else []
        missing_ctx = ai_result.get("missing_context", []) if ai_result else []

        questions: List[ReviewerQuestion] = []
        q_counter = 1

        # Question 1: Missing Evidence Questions
        for w in det_result.get("warnings", []):
            w_code = w.get("code", "")
            if "MISSING" in w_code or "NO_EVIDENCE" in w_code:
                questions.append(
                    ReviewerQuestion(
                        question_id=f"q_rev_{q_counter:02d}",
                        category="EVIDENCE_VERIFICATION",
                        question_text=f"What authoritative evidence artifact is required to verify rule check '{w_code}'?",
                        context_snippet=w.get("message"),
                    )
                )
                q_counter += 1

        # Question 2: Conflicting Evidence Questions
        for w in det_result.get("warnings", []):
            w_code = w.get("code", "")
            if "CONFLICT" in w_code:
                questions.append(
                    ReviewerQuestion(
                        question_id=f"q_rev_{q_counter:02d}",
                        category="EVIDENCE_CONFLICT",
                        question_text="Which source ledger record should be treated as authoritative to resolve this conflict?",
                        context_snippet=w.get("message"),
                    )
                )
                q_counter += 1

        # Question 3: AI Contradiction / Uncertainty Questions
        if ai_result:
            ai_rec = ai_result.get("recommendation", "")
            if ai_rec == "CONTRADICT":
                questions.append(
                    ReviewerQuestion(
                        question_id=f"q_rev_{q_counter:02d}",
                        category="AI_CONTRADICTION",
                        question_text="Does the customer history justify overriding the contextual AI contradiction?",
                        context_snippet=ai_summary,
                    )
                )
                q_counter += 1
            elif ai_rec == "UNCERTAIN":
                questions.append(
                    ReviewerQuestion(
                        question_id=f"q_rev_{q_counter:02d}",
                        category="AI_UNCERTAINTY",
                        question_text="Is additional merchant operational verification required to resolve contextual uncertainty?",
                        context_snippet=ai_summary,
                    )
                )
                q_counter += 1

        # Question 4: Financial Risk Questions
        if risk_level in ["HIGH", "CRITICAL"]:
            questions.append(
                ReviewerQuestion(
                    question_id=f"q_rev_{q_counter:02d}",
                    category="FINANCIAL_RISK",
                    question_text=f"Does the merchant authorize proposed financial exposure of INR {gross_inr:,.2f} (Risk Score: {risk_score:.2f})?",
                    context_snippet=f"Risk Level: {risk_level}, Score: {risk_score:.4f}",
                )
            )
            q_counter += 1

        if not questions:
            questions.append(
                ReviewerQuestion(
                    question_id="q_rev_01",
                    category="GENERAL_REVIEW",
                    question_text="Please review the proposed financial action parameters before manual authorization.",
                    context_snippet=f"Action: {action_type}, Amount: INR {gross_inr:,.2f}",
                )
            )

        return ReviewContext(
            decision_id=decision_id,
            proposed_action=f"{action_type} of INR {gross_inr:,.2f}",
            risk_summary={"level": risk_level, "score": risk_score},
            deterministic_findings_summary=det_findings,
            ai_assessment_summary=ai_summary,
            supporting_evidence_ids=supporting_ids,
            contradictory_evidence_items=contradictory_items,
            missing_context=missing_ctx,
            reviewer_questions=questions,
        )
