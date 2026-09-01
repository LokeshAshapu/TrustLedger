"""
TrustLedger Deterministic Finding Coverage & Benchmark Diagnostic Report CLI
Phase 3.1 Reconciled Verification Pipeline
"""

import argparse
import json
import os
import sys
from typing import Dict, List, Any
from verifier.deterministic.engine import DeterministicTrustEngine


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
    parser = argparse.ArgumentParser(description="TrustLedger Deterministic Diagnostics Runner")
    parser.add_argument("--input", default="data/splits/test.jsonl", help="Input decision requests JSONL file")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    args = parser.parse_args()

    processed_dir = os.path.join(args.data_dir, "processed")
    gt_dir = os.path.join(args.data_dir, "ground-truth")

    # 1. Load Observable Ledger Databases
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

    # 2. Load Hidden Ground Truth Labels for Diagnostics
    labels_db = load_jsonl_map(os.path.join(gt_dir, "labels.jsonl"), "decision_id")

    # 3. Instantiate Engine & Run Verification
    engine = DeterministicTrustEngine()
    test_decisions = load_jsonl_list(args.input)

    total_processed = len(test_decisions)
    hard_fail_count = 0
    warning_count = 0
    clean_pass_count = 0

    code_counts: Dict[str, int] = {}
    class_coverage: Dict[str, Dict[str, int]] = {}
    matrix: Dict[str, Dict[str, int]] = {}

    total_safe_cases = 0
    safe_hard_count = 0
    safe_warning_count = 0

    total_unsafe_detected_exposure_minor = 0

    for req in test_decisions:
        d_id = req["decision_id"]
        res = engine.verify(req, context)

        # Lookup ground truth ONLY for diagnostic reporting
        gt = labels_db.get(d_id, {})
        cls = gt.get("scenario_class", "UNKNOWN_CLASS")

        if cls not in class_coverage:
            class_coverage[cls] = {"total": 0, "hard_failures": 0, "warnings": 0, "no_findings": 0}
            matrix[cls] = {}

        class_coverage[cls]["total"] += 1

        if cls == "CLASS_A":
            total_safe_cases += 1
            if res.hard_failures:
                safe_hard_count += 1
            if res.warnings:
                safe_warning_count += 1

        if res.hard_failures:
            hard_fail_count += 1
            class_coverage[cls]["hard_failures"] += 1
            total_unsafe_detected_exposure_minor += res.potential_exposure.amount_minor
        elif res.warnings:
            warning_count += 1
            class_coverage[cls]["warnings"] += 1
        else:
            clean_pass_count += 1
            class_coverage[cls]["no_findings"] += 1

        for f in res.findings:
            code_counts[f.code] = code_counts.get(f.code, 0) + 1
            matrix[cls][f.code] = matrix[cls].get(f.code, 0) + 1

    # 4. Print Reconciled Diagnostic Report
    print("=" * 75)
    print("TrustLedger Deterministic Engine Benchmark Reconciliation (Phase 3.1)")
    print("=" * 75)
    print(f"Engine Version: trustledger.deterministic.v1")
    print(f"Test Input Dataset: {args.input}")
    print(f"Total Decisions Processed: {total_processed:,}")
    print("-" * 75)
    print(f"Cases with HARD Safety Failures: {hard_fail_count:,} ({hard_fail_count/total_processed*100:.1f}%)")
    print(f"Cases with WARNING Findings:     {warning_count:,} ({warning_count/total_processed*100:.1f}%)")
    print(f"Cases with Clean PASS (No Issue): {clean_pass_count:,} ({clean_pass_count/total_processed*100:.1f}%)")
    print("-" * 75)
    print("Benchmark Diagnostic Safety Metrics:")
    print(f"  - Safe HARD Finding Rate:        {safe_hard_count} / {total_safe_cases} ({safe_hard_count/total_safe_cases*100:.1f}%)")
    print(f"  - Safe Warning Rate:             {safe_warning_count} / {total_safe_cases} ({safe_warning_count/total_safe_cases*100:.1f}%)")
    print(f"  - Detected Exposure Potential:   INR {total_unsafe_detected_exposure_minor/100:,.2f}")
    print("-" * 75)
    print("Scenario Detection Coverage:")
    print(f"  {'Scenario Class':<15} | {'Total':<6} | {'HARD Fail':<9} | {'Warnings':<9} | {'No Findings':<11} | {'Coverage':<8}")
    print("  " + "-" * 70)
    for cls_name in sorted(class_coverage.keys()):
        cov = class_coverage[cls_name]
        det = cov['hard_failures'] + cov['warnings']
        pct = (det / cov['total'] * 100) if cov['total'] > 0 else 0.0
        print(
            f"  {cls_name:<15} | {cov['total']:<6} | {cov['hard_failures']:<9} | {cov['warnings']:<9} | {cov['no_findings']:<11} | {pct:>6.1f}%"
        )
    print("-" * 75)
    print("Finding-Level Confusion Matrix (Scenario Class vs Finding Code):")
    all_codes = sorted(code_counts.keys())
    header = f"  {'Scenario Class':<10}"
    print(header)
    print("  " + "-" * 70)
    for cls_name in sorted(matrix.keys()):
        row = matrix[cls_name]
        top_findings = [f"{c}:{cnt}" for c, cnt in sorted(row.items(), key=lambda x: x[1], reverse=True)[:3]]
        print(f"  {cls_name:<10} | {', '.join(top_findings)}")
    print("=" * 75)


if __name__ == "__main__":
    main()
