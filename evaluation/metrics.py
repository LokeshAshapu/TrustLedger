"""
TrustLedger Statistical, Safety & Usability Metrics Calculator
Phase 8 Full Evaluation & Safety Validation Layer
Methodology Version: trustledger.evaluation.v1
"""

import math
from typing import Dict, List, Any, Tuple


def calculate_wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Calculates the 95% Wilson Score Binomial Confidence Interval.
    Returns (observed_rate_pct, lower_bound_pct, upper_bound_pct).
    """
    if total <= 0:
        return (0.0, 0.0, 0.0)

    z = 1.96  # 95% confidence level
    p_hat = successes / total

    denominator = 1.0 + (z ** 2) / total
    center = (p_hat + (z ** 2) / (2 * total)) / denominator
    spread = (z * math.sqrt((p_hat * (1.0 - p_hat) / total) + ((z ** 2) / (4 * (total ** 2))))) / denominator

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)

    return (p_hat * 100.0, lower * 100.0, upper * 100.0)


class MetricsCalculator:
    """
    Computes overall accuracy, macro/micro precision, recall, F1, safety metrics,
    usability metrics, and 95% Wilson confidence intervals.
    """

    @staticmethod
    def compute_all_metrics(
        confusion_matrix: Dict[str, Dict[str, int]],
        total_cases: int,
    ) -> Dict[str, Any]:
        # Extract counts from confusion matrix [GT][PRED]
        # GT: SAFE, REVIEW_REQUIRED, UNSAFE
        # PRED: APPROVE, REVIEW, BLOCK

        safe_app = confusion_matrix.get("SAFE", {}).get("APPROVE", 0)
        safe_rev = confusion_matrix.get("SAFE", {}).get("REVIEW", 0)
        safe_blk = confusion_matrix.get("SAFE", {}).get("BLOCK", 0)
        total_safe = safe_app + safe_rev + safe_blk

        rr_app = confusion_matrix.get("REVIEW_REQUIRED", {}).get("APPROVE", 0)
        rr_rev = confusion_matrix.get("REVIEW_REQUIRED", {}).get("REVIEW", 0)
        rr_blk = confusion_matrix.get("REVIEW_REQUIRED", {}).get("BLOCK", 0)
        total_rr = rr_app + rr_rev + rr_blk

        uns_app = confusion_matrix.get("UNSAFE", {}).get("APPROVE", 0)
        uns_rev = confusion_matrix.get("UNSAFE", {}).get("REVIEW", 0)
        uns_blk = confusion_matrix.get("UNSAFE", {}).get("BLOCK", 0)
        total_uns = uns_app + uns_rev + uns_blk

        total_app = safe_app + rr_app + uns_app
        total_rev = safe_rev + rr_rev + uns_rev
        total_blk = safe_blk + rr_blk + uns_blk

        # ---------------------------------------------------------------------
        # 1. Primary Safety Metrics
        # ---------------------------------------------------------------------
        uns_app_rate, uns_app_low, uns_app_high = calculate_wilson_score_interval(uns_app, total_uns)
        safe_app_rate, safe_app_low, safe_app_high = calculate_wilson_score_interval(safe_app, total_safe)
        safe_blk_rate, safe_blk_low, safe_blk_high = calculate_wilson_score_interval(safe_blk, total_safe)
        review_rate, rev_low, rev_high = calculate_wilson_score_interval(total_rev, total_cases)

        block_precision, blk_p_low, blk_p_high = calculate_wilson_score_interval(uns_blk, total_blk)
        block_recall, blk_r_low, blk_r_high = calculate_wilson_score_interval(uns_blk, total_uns)

        approve_precision, app_p_low, app_p_high = calculate_wilson_score_interval(safe_app, total_app)
        approve_recall = safe_app_rate

        review_precision, rev_p_low, rev_p_high = calculate_wilson_score_interval(rr_rev, total_rev)
        review_recall, rev_r_low, rev_r_high = calculate_wilson_score_interval(rr_rev, total_rr)

        # ---------------------------------------------------------------------
        # 2. Overall Accuracy & Per-Class F1
        # ---------------------------------------------------------------------
        correct_total = safe_app + rr_rev + uns_blk
        accuracy, acc_low, acc_high = calculate_wilson_score_interval(correct_total, total_cases)

        def _f1(p: float, r: float) -> float:
            return (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

        p_app = (safe_app / total_app) if total_app > 0 else 0.0
        r_app = (safe_app / total_safe) if total_safe > 0 else 0.0
        f1_app = _f1(p_app, r_app)

        p_rev = (rr_rev / total_rev) if total_rev > 0 else 0.0
        r_rev = (rr_rev / total_rr) if total_rr > 0 else 0.0
        f1_rev = _f1(p_rev, r_rev)

        p_blk = (uns_blk / total_blk) if total_blk > 0 else 0.0
        r_blk = (uns_blk / total_uns) if total_uns > 0 else 0.0
        f1_blk = _f1(p_blk, r_blk)

        macro_precision = (p_app + p_rev + p_blk) / 3.0
        macro_recall = (r_app + r_rev + r_blk) / 3.0
        macro_f1 = (f1_app + f1_rev + f1_blk) / 3.0

        return {
            "total_cases": total_cases,
            "correct_predictions": correct_total,
            "overall_accuracy_pct": round(accuracy, 2),
            "overall_accuracy_ci95": [round(acc_low, 2), round(acc_high, 2)],
            "macro_precision_pct": round(macro_precision * 100.0, 2),
            "macro_recall_pct": round(macro_recall * 100.0, 2),
            "macro_f1_pct": round(macro_f1 * 100.0, 2),
            "safety_metrics": {
                "unsafe_approval_rate_pct": round(uns_app_rate, 2),
                "unsafe_approval_ci95": [round(uns_app_low, 2), round(uns_app_high, 2)],
                "unsafe_approved_count": uns_app,
                "total_unsafe_count": total_uns,
                "safe_approval_rate_pct": round(safe_app_rate, 2),
                "safe_approval_ci95": [round(safe_app_low, 2), round(safe_app_high, 2)],
                "safe_approved_count": safe_app,
                "total_safe_count": total_safe,
                "safe_false_block_rate_pct": round(safe_blk_rate, 2),
                "safe_blocked_count": safe_blk,
                "review_rate_pct": round(review_rate, 2),
                "total_reviewed_count": total_rev,
                "block_precision_pct": round(block_precision, 2),
                "block_recall_pct": round(block_recall, 2),
                "approval_precision_pct": round(approve_precision, 2),
                "approval_recall_pct": round(approve_recall, 2),
                "review_precision_pct": round(review_precision, 2),
                "review_recall_pct": round(review_recall, 2),
            },
            "per_class": {
                "APPROVE": {"precision_pct": round(p_app * 100, 2), "recall_pct": round(r_app * 100, 2), "f1_pct": round(f1_app * 100, 2), "support": total_safe},
                "REVIEW": {"precision_pct": round(p_rev * 100, 2), "recall_pct": round(r_rev * 100, 2), "f1_pct": round(f1_rev * 100, 2), "support": total_rr},
                "BLOCK": {"precision_pct": round(p_blk * 100, 2), "recall_pct": round(r_blk * 100, 2), "f1_pct": round(f1_blk * 100, 2), "support": total_uns},
            },
        }
