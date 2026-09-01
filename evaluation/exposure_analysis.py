"""
TrustLedger Financial Exposure Evaluator
Phase 8 Full Evaluation & Safety Validation Layer
"""

from typing import Dict, List, Any


class ExposureAnalyzer:
    """
    Analyzes financial exposure distribution across predicted verdicts for UNSAFE cases.
    """

    @staticmethod
    def analyze_exposure(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_unsafe_exp_minor = 0
        unsafe_approved_exp_minor = 0
        unsafe_blocked_exp_minor = 0
        unsafe_reviewed_exp_minor = 0

        for r in results:
            if r.get("ground_truth_verdict") == "UNSAFE":
                exp_minor = r.get("gross_exposure_minor", 0)
                total_unsafe_exp_minor += exp_minor
                pred = r.get("predicted_verdict")

                if pred == "APPROVE":
                    unsafe_approved_exp_minor += exp_minor
                elif pred == "BLOCK":
                    unsafe_blocked_exp_minor += exp_minor
                elif pred == "REVIEW":
                    unsafe_reviewed_exp_minor += exp_minor

        total_inr = total_unsafe_exp_minor / 100.0
        approved_inr = unsafe_approved_exp_minor / 100.0
        blocked_inr = unsafe_blocked_exp_minor / 100.0
        reviewed_inr = unsafe_reviewed_exp_minor / 100.0

        return {
            "total_unsafe_exposure_minor": total_unsafe_exp_minor,
            "total_unsafe_exposure_inr": total_inr,
            "unsafe_exposure_approved": {
                "amount_minor": unsafe_approved_exp_minor,
                "amount_inr": approved_inr,
                "percentage": (unsafe_approved_exp_minor / total_unsafe_exp_minor * 100.0) if total_unsafe_exp_minor > 0 else 0.0,
            },
            "unsafe_exposure_blocked": {
                "amount_minor": unsafe_blocked_exp_minor,
                "amount_inr": blocked_inr,
                "percentage": (unsafe_blocked_exp_minor / total_unsafe_exp_minor * 100.0) if total_unsafe_exp_minor > 0 else 0.0,
                "description": "Potential exposure blocked in benchmark simulation.",
            },
            "unsafe_exposure_reviewed": {
                "amount_minor": unsafe_reviewed_exp_minor,
                "amount_inr": reviewed_inr,
                "percentage": (unsafe_reviewed_exp_minor / total_unsafe_exp_minor * 100.0) if total_unsafe_exp_minor > 0 else 0.0,
            },
        }
