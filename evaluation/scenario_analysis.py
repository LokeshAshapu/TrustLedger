"""
TrustLedger Disaggregated Scenario, Action, Difficulty & Risk Analyzer
Phase 8 Full Evaluation & Safety Validation Layer
"""

from typing import Dict, List, Any


class ScenarioAnalyzer:
    """
    Performs disaggregated performance analysis across scenario classes (A-J),
    action types, difficulty levels, risk bands, and AI contribution.
    """

    @staticmethod
    def analyze_scenarios(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        scenarios: Dict[str, Dict[str, Any]] = {}
        for r in results:
            s_class = r.get("scenario_class", "CLASS_UNKNOWN")
            if s_class not in scenarios:
                scenarios[s_class] = {
                    "total_count": 0,
                    "expected_verdict": r.get("expected_verdict", "UNKNOWN"),
                    "verdict_counts": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
                    "exact_matches": 0,
                    "unsafe_approvals": 0,
                    "false_blocks": 0,
                    "total_exposure_minor": 0,
                    "approved_exposure_minor": 0,
                    "blocked_exposure_minor": 0,
                    "reviewed_exposure_minor": 0,
                }

            sc = scenarios[s_class]
            sc["total_count"] += 1
            pred = r.get("predicted_verdict", "UNKNOWN")
            sc["verdict_counts"][pred] = sc["verdict_counts"].get(pred, 0) + 1

            exp_minor = r.get("gross_exposure_minor", 0)
            sc["total_exposure_minor"] += exp_minor

            if pred == "APPROVE":
                sc["approved_exposure_minor"] += exp_minor
            elif pred == "BLOCK":
                sc["blocked_exposure_minor"] += exp_minor
            elif pred == "REVIEW":
                sc["reviewed_exposure_minor"] += exp_minor

            gt = r.get("ground_truth_verdict")
            expected_v = r.get("expected_verdict")

            if pred == expected_v:
                sc["exact_matches"] += 1

            if gt == "UNSAFE" and pred == "APPROVE":
                sc["unsafe_approvals"] += 1
            elif gt == "SAFE" and pred == "BLOCK":
                sc["false_blocks"] += 1

        # Format scenario summaries
        scenario_metrics = {}
        for s_class, sc in sorted(scenarios.items()):
            tot = sc["total_count"]
            scenario_metrics[s_class] = {
                "total_count": tot,
                "expected_verdict": sc["expected_verdict"],
                "verdict_counts": sc["verdict_counts"],
                "exact_match_rate_pct": round(sc["exact_matches"] / tot * 100.0, 2) if tot > 0 else 0.0,
                "unsafe_approvals": sc["unsafe_approvals"],
                "false_blocks": sc["false_blocks"],
                "total_exposure_inr": sc["total_exposure_minor"] / 100.0,
                "approved_exposure_inr": sc["approved_exposure_minor"] / 100.0,
                "blocked_exposure_inr": sc["blocked_exposure_minor"] / 100.0,
                "reviewed_exposure_inr": sc["reviewed_exposure_minor"] / 100.0,
            }

        return scenario_metrics

    @staticmethod
    def analyze_actions(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        actions: Dict[str, Dict[str, Any]] = {}
        for r in results:
            act = r.get("action_type", "UNKNOWN")
            if act not in actions:
                actions[act] = {
                    "total_count": 0,
                    "verdict_counts": {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0},
                    "unsafe_count": 0,
                    "unsafe_approvals": 0,
                    "safe_count": 0,
                    "false_blocks": 0,
                    "scores": [],
                    "total_exposure_minor": 0,
                }

            a = actions[act]
            a["total_count"] += 1
            pred = r.get("predicted_verdict", "UNKNOWN")
            a["verdict_counts"][pred] = a["verdict_counts"].get(pred, 0) + 1
            a["scores"].append(r.get("risk_score", 0.0))
            a["total_exposure_minor"] += r.get("gross_exposure_minor", 0)

            gt = r.get("ground_truth_verdict")
            if gt == "UNSAFE":
                a["unsafe_count"] += 1
                if pred == "APPROVE":
                    a["unsafe_approvals"] += 1
            elif gt == "SAFE":
                a["safe_count"] += 1
                if pred == "BLOCK":
                    a["false_blocks"] += 1

        action_metrics = {}
        for act, a in sorted(actions.items()):
            tot = a["total_count"]
            action_metrics[act] = {
                "total_count": tot,
                "verdict_counts": a["verdict_counts"],
                "unsafe_approval_rate_pct": round(a["unsafe_approvals"] / max(1, a["unsafe_count"]) * 100.0, 2),
                "false_block_rate_pct": round(a["false_blocks"] / max(1, a["safe_count"]) * 100.0, 2),
                "average_risk_score": round(sum(a["scores"]) / max(1, tot), 4),
                "total_exposure_inr": a["total_exposure_minor"] / 100.0,
            }

        return action_metrics

    @staticmethod
    def analyze_difficulty(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        diffs: Dict[str, Dict[str, Any]] = {}
        for r in results:
            d = r.get("difficulty", "UNKNOWN")
            if d not in diffs:
                diffs[d] = {
                    "total_count": 0,
                    "exact_matches": 0,
                    "unsafe_count": 0,
                    "unsafe_approvals": 0,
                    "safe_count": 0,
                    "false_blocks": 0,
                    "reviews": 0,
                    "approved_exp_minor": 0,
                    "blocked_exp_minor": 0,
                }

            df = diffs[d]
            df["total_count"] += 1
            pred = r.get("predicted_verdict", "UNKNOWN")
            expected_v = r.get("expected_verdict")
            exp_minor = r.get("gross_exposure_minor", 0)

            if pred == expected_v:
                df["exact_matches"] += 1

            if pred == "REVIEW":
                df["reviews"] += 1
            elif pred == "APPROVE":
                df["approved_exp_minor"] += exp_minor
            elif pred == "BLOCK":
                df["blocked_exp_minor"] += exp_minor

            gt = r.get("ground_truth_verdict")
            if gt == "UNSAFE":
                df["unsafe_count"] += 1
                if pred == "APPROVE":
                    df["unsafe_approvals"] += 1
            elif gt == "SAFE":
                df["safe_count"] += 1
                if pred == "BLOCK":
                    df["false_blocks"] += 1

        diff_metrics = {}
        for d, df in sorted(diffs.items()):
            tot = df["total_count"]
            diff_metrics[d] = {
                "total_count": tot,
                "decision_accuracy_pct": round(df["exact_matches"] / tot * 100.0, 2) if tot > 0 else 0.0,
                "unsafe_approval_rate_pct": round(df["unsafe_approvals"] / max(1, df["unsafe_count"]) * 100.0, 2),
                "false_block_rate_pct": round(df["false_blocks"] / max(1, df["safe_count"]) * 100.0, 2),
                "review_rate_pct": round(df["reviews"] / tot * 100.0, 2) if tot > 0 else 0.0,
                "approved_exposure_inr": df["approved_exp_minor"] / 100.0,
                "blocked_exposure_inr": df["blocked_exp_minor"] / 100.0,
            }

        return diff_metrics
