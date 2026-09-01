"""
TrustLedger 3x3 Confusion Matrix Generator
Phase 8 Full Evaluation & Safety Validation Layer
"""

from typing import Dict, List, Any


class ConfusionMatrixGenerator:
    """
    Generates structured 3x3 confusion matrix mapping ground-truth labels
    (SAFE, REVIEW_REQUIRED, UNSAFE) against predicted verdicts (APPROVE, REVIEW, BLOCK).
    """

    @staticmethod
    def build_matrix(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        matrix = {
            "SAFE": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
            "REVIEW_REQUIRED": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
            "UNSAFE": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
        }

        for r in results:
            gt = r.get("ground_truth_verdict", "UNKNOWN")
            pred = r.get("predicted_verdict", "UNKNOWN")
            if gt in matrix and pred in matrix[gt]:
                matrix[gt][pred] += 1

        return matrix

    @staticmethod
    def render_markdown_table(matrix: Dict[str, Dict[str, int]]) -> str:
        s = "### 3x3 Verdict Confusion Matrix\n\n"
        s += "| Expected Ground Truth | Predicted APPROVE | Predicted REVIEW | Predicted BLOCK | Total |\n"
        s += "| :--- | :---: | :---: | :---: | :---: |\n"

        for gt in ["SAFE", "REVIEW_REQUIRED", "UNSAFE"]:
            row = matrix.get(gt, {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0})
            total = row["APPROVE"] + row["REVIEW"] + row["BLOCK"]
            s += f"| **{gt}** | {row['APPROVE']:,} | {row['REVIEW']:,} | {row['BLOCK']:,} | {total:,} |\n"

        return s
