"""
TrustLedger Canonical Evaluation Snapshot Module
Phase 10D Evaluation Truth & Buildathon Readiness
"""

from typing import Dict, Any

CANONICAL_EVALUATION_SNAPSHOT: Dict[str, Any] = {
    "metadata": {
        "evaluation_version": "trustledger.evaluation.v1",
        "gate_version": "trustledger.decision-gate.v1",
        "dataset_input": "data/splits/test.jsonl",
        "total_cases": 1500,
        "dataset_seed": 42,
        "reproducible_2pass": True,
        "ground_truth_isolated": True,
    },
    "metrics": {
        "total_cases": 1500,
        "correct_predictions": 1436,
        "overall_accuracy_pct": 95.73,
        "overall_accuracy_ci95": [94.59, 96.64],
        "macro_precision_pct": 96.96,
        "macro_recall_pct": 94.71,
        "macro_f1_pct": 95.65,
        "safety_metrics": {
            "unsafe_approval_rate_pct": 0.0,
            "unsafe_approval_ci95": [0.0, 0.6],
            "unsafe_approved_count": 0,
            "total_unsafe_count": 637,
            "safe_approval_rate_pct": 93.98,
            "safe_approval_ci95": [91.66, 95.68],
            "safe_approved_count": 515,
            "total_safe_count": 548,
            "safe_false_block_rate_pct": 6.02,
            "safe_blocked_count": 33,
            "review_rate_pct": 18.93,
            "total_reviewed_count": 284,
            "block_precision_pct": 90.87,
            "block_recall_pct": 100.0,
            "approval_precision_pct": 100.0,
            "approval_recall_pct": 93.98,
            "review_precision_pct": 100.0,
            "review_recall_pct": 90.16,
        },
        "per_class": {
            "APPROVE": {
                "precision_pct": 100.0,
                "recall_pct": 93.98,
                "f1_pct": 96.9,
                "support": 548,
            },
            "REVIEW": {
                "precision_pct": 100.0,
                "recall_pct": 90.16,
                "f1_pct": 94.82,
                "support": 315,
            },
            "BLOCK": {
                "precision_pct": 90.87,
                "recall_pct": 100.0,
                "f1_pct": 95.22,
                "support": 637,
            },
        },
    },
    "confusion_matrix": {
        "SAFE": {"APPROVE": 515, "REVIEW": 0, "BLOCK": 33},
        "REVIEW_REQUIRED": {"APPROVE": 0, "REVIEW": 284, "BLOCK": 31},
        "UNSAFE": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 637},
    },
    "exposure_metrics": {
        "total_unsafe_exposure_minor": 977447800,
        "total_unsafe_exposure_inr": 9774478.0,
        "unsafe_exposure_approved": {
            "amount_minor": 0,
            "amount_inr": 0.0,
            "percentage": 0.0,
        },
        "unsafe_exposure_blocked": {
            "amount_minor": 977447800,
            "amount_inr": 9774478.0,
            "percentage": 100.0,
            "description": "Potential exposure blocked in benchmark simulation.",
        },
        "unsafe_exposure_reviewed": {
            "amount_minor": 0,
            "amount_inr": 0.0,
            "percentage": 0.0,
        },
    },
    "adversarial_suite": {
        "total_vectors": 10,
        "passed_vectors": 10,
        "pass_rate_pct": 100.0,
        "vectors": [
            "Vector_A_Prompt_Injection",
            "Vector_B_Fake_Evidence_Citation",
            "Vector_C_Confidence_Manipulation",
            "Vector_D_Invalid_AI_Recommendation",
            "Vector_E_AI_Support_Against_Hard_Failure",
            "Vector_F_Tampered_Decision_Hash",
            "Vector_G_Tampered_Amount",
            "Vector_H_Tampered_Currency",
            "Vector_I_Authorization_Replay",
            "Vector_J_Expired_Authorization",
        ],
    },
    "financial_invariants": {
        "total_invariants": 9,
        "passed_invariants": 9,
        "pass_rate_pct": 100.0,
    },
}
