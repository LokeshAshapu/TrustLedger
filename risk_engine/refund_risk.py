"""
TrustLedger Refund Risk Taxonomy & Exposure Analysis Module
Phase 11A AI Refund Risk Manager Specialization
"""

from typing import Dict, Any, List
from verifier.deterministic.models import FindingSeverity
from risk_engine.models import RiskCategory, RiskAssessment


# Dedicated Refund Risk Taxonomy Codes & Definitions
REFUND_RISK_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "REFUND_AMOUNT_MISMATCH": {
        "code": "REFUND_AMOUNT_MISMATCH",
        "name": "Refund Amount Mismatch",
        "category": RiskCategory.FINANCIAL,
        "severity": FindingSeverity.HARD,
        "expected_verdict": "BLOCK",
        "description": "Requested refund amount exceeds valid transaction or refundable balance.",
    },
    "DUPLICATE_REFUND": {
        "code": "DUPLICATE_REFUND",
        "name": "Duplicate Refund Attempt",
        "category": RiskCategory.ACTION,
        "severity": FindingSeverity.HARD,
        "expected_verdict": "BLOCK",
        "description": "A refund has already been issued or an equivalent refund action is recorded.",
    },
    "POLICY_CAP_VIOLATION": {
        "code": "POLICY_CAP_VIOLATION",
        "name": "Merchant Refund Policy Cap Breach",
        "category": RiskCategory.POLICY,
        "severity": FindingSeverity.HARD,
        "expected_verdict": "BLOCK",
        "description": "Requested automatic refund exceeds merchant's configured automatic refund cap (e.g. ₹60,000 vs ₹25,000 limit).",
    },
    "ENTITY_MISMATCH": {
        "code": "ENTITY_MISMATCH",
        "name": "Customer / Order Entity Mismatch",
        "category": RiskCategory.CONSISTENCY,
        "severity": FindingSeverity.HARD,
        "expected_verdict": "BLOCK",
        "description": "Customer, order, or transaction entity relationship does not match authoritative records.",
    },
    "NONEXISTENT_TRANSACTION": {
        "code": "NONEXISTENT_TRANSACTION",
        "name": "Nonexistent Transaction Reference",
        "category": RiskCategory.CONSISTENCY,
        "severity": FindingSeverity.HARD,
        "expected_verdict": "BLOCK",
        "description": "Referenced transaction ID cannot be verified in transaction repository.",
    },
    "MISSING_EVIDENCE": {
        "code": "MISSING_EVIDENCE",
        "name": "Missing Required Evidence",
        "category": RiskCategory.EVIDENCE,
        "severity": FindingSeverity.WARNING,
        "expected_verdict": "REVIEW",
        "description": "Required supporting evidence artifact is absent.",
    },
    "CONFLICTING_EVIDENCE": {
        "code": "CONFLICTING_EVIDENCE",
        "name": "Conflicting Evidence Signals",
        "category": RiskCategory.EVIDENCE,
        "severity": FindingSeverity.WARNING,
        "expected_verdict": "REVIEW",
        "description": "Two trusted evidence sources disagree (e.g. Courier API vs Customer Support Log).",
    },
    "STALE_EVIDENCE": {
        "code": "STALE_EVIDENCE",
        "name": "Stale Evidence (>30 Days)",
        "category": RiskCategory.TEMPORAL,
        "severity": FindingSeverity.WARNING,
        "expected_verdict": "REVIEW",
        "description": "Evidence timestamp exceeds configured freshness threshold (>30 days old).",
    },
    "REFUND_VELOCITY_RISK": {
        "code": "REFUND_VELOCITY_RISK",
        "name": "High Customer Refund Velocity",
        "category": RiskCategory.TEMPORAL,
        "severity": FindingSeverity.WARNING,
        "expected_verdict": "REVIEW",
        "description": "Unusually high refund frequency associated with customer context within recent window.",
    },
}


def build_refund_risk_summary(
    risk_assessment: RiskAssessment, request_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extracts refund-specific financial exposure metrics and risk taxonomy breakdown
    for Buildathon UI presentation.
    """
    amount = request_payload.get("amount", {})
    requested_minor = amount.get("amount_minor", 0)
    currency = amount.get("currency", "INR")

    # Policy cap limit from context or default ₹25,000 (2,500,000 minor)
    policy_cap_minor = 2500000
    policy_diff_minor = max(0, requested_minor - policy_cap_minor)

    return {
        "action_type": "REFUND",
        "requested_refund_minor": requested_minor,
        "requested_refund_inr": requested_minor / 100.0,
        "currency": currency,
        "policy_cap_minor": policy_cap_minor,
        "policy_cap_inr": policy_cap_minor / 100.0,
        "policy_difference_minor": policy_diff_minor,
        "policy_difference_inr": policy_diff_minor / 100.0,
        "is_cap_breached": requested_minor > policy_cap_minor,
        "potential_exposure_minor": requested_minor,
        "irreversible_exposure_minor": (
            0 if risk_assessment.risk_level.value in ["HIGH", "CRITICAL"] else requested_minor
        ),
        "refund_risk_score": risk_assessment.risk_score,
        "refund_risk_level": risk_assessment.risk_level.value,
        "hard_risk_flags": risk_assessment.hard_risk_flags,
        "warnings": risk_assessment.warnings,
    }
