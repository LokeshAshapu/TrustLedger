"""
TrustLedger Deterministic Financial Risk Diagnostics & Benchmark Analysis CLI
Phase 4 Deterministic Financial Risk Layer
Methodology Version: trustledger.risk.v1
"""

import argparse
import json
import os
import time
import statistics
from typing import Dict, List, Any

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine


def load_jsonl_map(file_path: str, key_field: str) -> Dict[str, Dict[str, Any]]:
    m = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    m[rec[key_field]] = rec
    return m


def load_jsonl_list(file_path: str) -> List[Dict[str, Any]]:
    lst = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    lst.append(json.loads(line))
    return lst


def main():
    parser = argparse.ArgumentParser(description="TrustLedger Risk Engine Diagnostics Runner")
    parser.add_argument("--input", default="data/splits/test.jsonl", help="Path to input test split JSONL")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    args = parser.parse_args()

    processed_dir = os.path.join(args.data_dir, "processed")
    gt_dir = os.path.join(args.data_dir, "ground-truth")

    # 1. Load Observable Databases
    evidence_db = load_jsonl_map(os.path.join(processed_dir, "evidence.jsonl"), "evidence_id")
    transactions_db = load_jsonl_map(os.path.join(processed_dir, "transactions.jsonl"), "transaction_id")
    orders_db = load_jsonl_map(os.path.join(processed_dir, "orders.jsonl"), "order_id")
    customers_db = load_jsonl_map(os.path.join(processed_dir, "customers.jsonl"), "customer_id")
    policies_db = load_jsonl_map(os.path.join(processed_dir, "policies.jsonl"), "merchant_id")
    refund_history_db = load_jsonl_list(os.path.join(processed_dir, "refunds.jsonl"))

    context = {
        "evidence_db": evidence_db,
        "transactions_db": transactions_db,
        "orders_db": orders_db,
        "customers_db": customers_db,
        "policy_snapshots_db": policies_db,
        "refund_history_db": refund_history_db,
    }

    # 2. Load Hidden Ground Truth Labels ONLY for Diagnostic Analysis
    labels_db = load_jsonl_map(os.path.join(gt_dir, "labels.jsonl"), "decision_id")

    # 3. Instantiate Engines
    det_engine = DeterministicTrustEngine()
    risk_engine = FinancialRiskEngine()

    test_decisions = load_jsonl_list(args.input)
    total_processed = len(test_decisions)

    level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    scores = []
    total_gross_exposure_minor = 0
    total_incremental_exposure_minor = 0
    total_irreversible_exposure_minor = 0

    exposure_by_level = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    action_by_level: Dict[str, Dict[str, int]] = {}

    factor_counts: Dict[str, int] = {}
    flag_counts: Dict[str, int] = {}

    # Diagnostic comparison arrays against hidden ground truth
    gt_scores: Dict[str, List[float]] = {"SAFE": [], "UNSAFE": [], "REVIEW_REQUIRED": []}

    start_time = time.time()

    for req in test_decisions:
        d_id = req["decision_id"]
        action_type = req.get("action_type", "REFUND")

        # Run Phase 3 Deterministic Engine
        det_res = det_engine.verify(req, context)

        # Run Phase 4 Financial Risk Engine
        risk_res = risk_engine.assess(req, context, det_res)

        level = risk_res.risk_level.value
        score = risk_res.risk_score

        level_counts[level] += 1
        scores.append(score)

        gross_m = risk_res.exposure.gross_exposure.amount_minor
        inc_m = risk_res.exposure.incremental_exposure.amount_minor
        irrev_m = risk_res.exposure.irreversible_exposure.amount_minor

        total_gross_exposure_minor += gross_m
        total_incremental_exposure_minor += inc_m
        total_irreversible_exposure_minor += irrev_m
        exposure_by_level[level] += gross_m

        if action_type not in action_by_level:
            action_by_level[action_type] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        action_by_level[action_type][level] += 1

        for f in risk_res.factors:
            factor_counts[f.factor_code] = factor_counts.get(f.factor_code, 0) + 1

        for flag in risk_res.hard_risk_flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

        # Diagnostic ground-truth comparison
        gt = labels_db.get(d_id, {})
        gt_verdict = gt.get("ground_truth_verdict")
        if gt_verdict in gt_scores:
            gt_scores[gt_verdict].append(score)

    elapsed_ms = (time.time() - start_time) * 1000

    # 4. Print Risk Engine Diagnostic Report
    print("=" * 75)
    print("TrustLedger Financial Risk Engine Diagnostic Report (Phase 4)")
    print("=" * 75)
    print(f"Methodology Version: trustledger.risk.v1")
    print(f"Test Input Dataset: {args.input}")
    print(f"Total Decisions Assessed: {total_processed:,}")
    print(f"Total Execution Runtime:  {elapsed_ms:.2f} ms ({elapsed_ms/total_processed:.3f} ms/decision)")
    print("-" * 75)
    print("Risk Level Distribution:")
    for lvl in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        cnt = level_counts[lvl]
        print(f"  - {lvl:<10}: {cnt:,} ({cnt/total_processed*100:.1f}%)")
    print("-" * 75)
    print("Risk Score Summary:")
    print(f"  - Average Score: {statistics.mean(scores):.4f}")
    print(f"  - Median Score:  {statistics.median(scores):.4f}")
    print(f"  - Min Score:     {min(scores):.4f}")
    print(f"  - Max Score:     {max(scores):.4f}")
    print("-" * 75)
    print("Financial Exposure Summary:")
    print(f"  - Total Gross Exposure:         INR {total_gross_exposure_minor/100:,.2f}")
    print(f"  - Total Incremental Exposure:   INR {total_incremental_exposure_minor/100:,.2f}")
    print(f"  - Total Irreversible Exposure:  INR {total_irreversible_exposure_minor/100:,.2f}")
    print("Gross Exposure Breakdown by Risk Level:")
    for lvl in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        exp = exposure_by_level[lvl]
        print(f"  - {lvl:<10}: INR {exp/100:,.2f} ({exp/total_gross_exposure_minor*100:.1f}%)")
    print("-" * 75)
    print("Risk Level Breakdown by Action Type:")
    print(f"  {'Action Type':<18} | {'LOW':<6} | {'MEDIUM':<6} | {'HIGH':<6} | {'CRITICAL':<8}")
    print("  " + "-" * 55)
    for act in sorted(action_by_level.keys()):
        b = action_by_level[act]
        print(f"  {act:<18} | {b['LOW']:<6} | {b['MEDIUM']:<6} | {b['HIGH']:<6} | {b['CRITICAL']:<8}")
    print("-" * 75)
    print("Hard Risk Flags Frequency:")
    for flag, cnt in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {flag:<30}: {cnt:,}")
    print("-" * 75)
    print("Benchmark Diagnostic Analysis (Score Comparison by Ground-Truth Verdict):")
    for gtv, gscores in gt_scores.items():
        if gscores:
            print(f"  - Ground Truth {gtv:<16}: Avg Score = {statistics.mean(gscores):.4f} | Median = {statistics.median(gscores):.4f} (Count: {len(gscores):,})")
    print("=" * 75)


if __name__ == "__main__":
    main()
