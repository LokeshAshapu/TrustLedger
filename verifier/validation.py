"""
TrustLedger AI Result Schema & Citation Validation Engine
Phase 5 AI Contextual Verification Layer
"""

from typing import Dict, Any, List
from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    DeterministicConflictItem,
)


class AIValidationEngine:
    """
    Validates AI model response JSON, enforces schema compliance, bounds confidence,
    and verifies evidence citations against the input verification packet.
    """

    def validate(self, raw_json: Dict[str, Any], packet: AIVerificationPacket) -> AIVerificationResult:
        # 1. Schema Contract Validation via Pydantic
        result = AIVerificationResult.model_validate(raw_json)

        # 2. Strict Recommendation Boundary (Cannot emit APPROVE/REVIEW/BLOCK)
        if result.recommendation not in [AIRecommendation.SUPPORT, AIRecommendation.UNCERTAIN, AIRecommendation.CONTRADICT]:
            raise ValueError(f"Invalid AI recommendation '{result.recommendation}'. Must be SUPPORT, UNCERTAIN, or CONTRADICT.")

        # 3. Evidence Citation Verification
        valid_ev_ids = {e.get("evidence_id") for e in packet.relevant_evidence if isinstance(e, dict) and "evidence_id" in e}

        for ev_id in result.supporting_evidence:
            if valid_ev_ids and ev_id not in valid_ev_ids:
                raise ValueError(f"AI result cited nonexistent supporting evidence ID '{ev_id}' not found in verification packet.")

        for item in result.contradictory_evidence:
            if valid_ev_ids and item.evidence_id not in valid_ev_ids:
                raise ValueError(f"AI result cited nonexistent contradictory evidence ID '{item.evidence_id}' not found in verification packet.")

        # 4. Preserve HARD Deterministic Findings acknowledgment
        det_res = packet.deterministic_result
        hard_failures = det_res.get("hard_failures", []) if isinstance(det_res, dict) else []

        if hard_failures:
            hard_codes = {h.get("code") for h in hard_failures if isinstance(h, dict)}
            ack_codes = {c.finding_code for c in result.deterministic_conflicts}

            # Automatically inject acknowledgment if model missed explicitly citing it
            for h in hard_failures:
                h_code = h.get("code")
                if h_code and h_code not in ack_codes:
                    result.deterministic_conflicts.append(
                        DeterministicConflictItem(
                            finding_code=h_code,
                            acknowledged=True,
                            explanation=f"System enforced acknowledgment of HARD safety failure '{h_code}'.",
                        )
                    )

        return result
