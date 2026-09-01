"""
TrustLedger Decision Gate Full Benchmark Evaluation & Diagnostics CLI
Phase 6 Signal Aggregation & Decision Layer
Gate Version: trustledger.decision-gate.v1
"""

import argparse
import json
import os
import time
import statistics
from typing import Dict, List, Any

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine
from verifier.packet_builder import AIVerificationPacketBuilder
from verifier.service import AIVerificationService
from verifier.providers.mock_provider import MockLLMProvider
from verifier.providers.nvidia_provider import NVIDIAProvider
from decision_gate.gate import DecisionGate


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
    parser = argparse.ArgumentParser(description="TrustLedger Full Pipeline Benchmark Evaluation Tool")
    parser.add_argument("--input", default="data/splits/test.jsonl", help="Path to input test split JSONL")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    args = parser.parse_args()

    processed_dir = os.path.join(args.data_dir, "processed")
    gt_dir = os.path.join(args.data_dir, "ground-truth")

    # Load Observable Context
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

    # Load Hidden Ground-Truth Labels ONLY for Evaluation Script
    labels_db = load_jsonl_map(os.path.join(gt_dir, "labels.jsonl"), "decision_id")

    # Instantiate Pipeline Engines
    det_engine = DeterministicTrustEngine()
    risk_engine = FinancialRiskEngine()

    if os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY"):
        try:
            ai_service = AIVerificationService(NVIDIAProvider())
        except Exception:
            ai_service = AIVerificationService(MockLLMProvider())
    else:
        ai_service = AIVerificationService(MockLLMProvider())

    gate = DecisionGate()

    test_decisions = load_jsonl_list(args.input)
    total_processed = len(test_decisions)

    verdict_counts = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
    rule_counts: Dict[str, int] = {}
    class_matrix: Dict[str, Dict[str, int]] = {}

    # Metric tracking
    total_unsafe_count = 0
    unsafe_approved_count = 0
    unsafe_blocked_count = 0
    unsafe_reviewed_count = 0

    total_safe_count = 0
    safe_approved_count = 0
    safe_blocked_count = 0
    safe_reviewed_count = 0

    total_review_required_count = 0
    review_req_reviewed_count = 0

    # Financial Exposure metrics (in minor units / paise)
    total_unsafe_exp_minor = 0
    unsafe_approved_exp_minor = 0
    unsafe_blocked_exp_minor = 0
    unsafe_reviewed_exp_minor = 0

    latencies = []
    start_time = time.time()

    for req in test_decisions:
        d_id = req["decision_id"]
        gt = labels_db.get(d_id, {})
        gt_verdict = gt.get("ground_truth_verdict", "UNKNOWN")
        expected_gate_verdict = gt.get("expected_verdict", "REVIEW")
        s_class = gt.get("scenario_class", "CLASS_UNKNOWN")

        step_t = time.time()

        # Step 1: Deterministic Engine
        det_res = det_engine.verify(req, context)

        # Step 2: Risk Engine
        risk_res = risk_engine.assess(req, context, det_res)

        # Step 3: AI Contextual Verifier
        packet = AIVerificationPacketBuilder.build(req, context, det_res, risk_res)
        ai_res = ai_service.verify_context(packet)

        # Step 4: Decision Gate
        gate_res = gate.evaluate(req, det_res, risk_res, ai_res)

        latencies.append((time.time() - step_t) * 1000)

        actual_v = gate_res.verdict.value
        verdict_counts[actual_v] += 1
        rule_counts[gate_res.decision_rule] = rule_counts.get(gate_res.decision_rule, 0) + 1

        if s_class not in class_matrix:
            class_matrix[s_class] = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
        class_matrix[s_class][actual_v] += 1

        # Ground-Truth Comparison Metrics
        req_exp_minor = risk_res.exposure.gross_exposure.amount_minor

        if gt_verdict == "UNSAFE":
            total_unsafe_count += 1
            total_unsafe_exp_minor += req_exp_minor
            if actual_v == "APPROVE":
                unsafe_approved_count += 1
                unsafe_approved_exp_minor += req_exp_minor
            elif actual_v == "BLOCK":
                unsafe_blocked_count += 1
                unsafe_blocked_exp_minor += req_exp_minor
            elif actual_v == "REVIEW":
                unsafe_reviewed_count += 1
                unsafe_reviewed_exp_minor += req_exp_minor

        elif gt_verdict == "SAFE":
            total_safe_count += 1
            if actual_v == "APPROVE":
                safe_approved_count += 1
            elif actual_v == "BLOCK":
                safe_blocked_count += 1
            elif actual_v == "REVIEW":
                safe_reviewed_count += 1

        elif gt_verdict == "REVIEW_REQUIRED":
            total_review_required_count += 1
            if actual_v == "REVIEW":
                review_req_reviewed_count += 1

    elapsed_s = time.time() - start_time

    # Key Safety Metrics Calculations
    unsafe_approval_rate = (unsafe_approved_count / total_unsafe_count * 100) if total_unsafe_count > 0 else 0.0
    safe_approval_rate = (safe_approved_count / total_safe_count * 100) if total_safe_count > 0 else 0.0
    review_rate = (verdict_counts["REVIEW"] / total_processed * 100)
    block_precision = (unsafe_blocked_count / verdict_counts["BLOCK"] * 100) if verdict_counts["BLOCK"] > 0 else 100.0

    # Decision Accuracy (matching expected verdict)
    correct_verdicts = safe_approved_count + unsafe_blocked_count + review_req_reviewed_count
    accuracy_pct = (correct_verdicts / total_processed * 100)

    print("=" * 75)
    print("TrustLedger Decision Gate Full Benchmark Diagnostic Report (Phase 6)")
    print("=" * 75)
    print(f"Gate Version:       {gate.version}")
    print(f"Test Input Dataset: {args.input}")
    print(f"Total Decisions:    {total_processed:,}")
    print(f"Total Runtime:      {elapsed_s:.2f} s ({statistics.mean(latencies):.2f} ms/decision)")
    print("-" * 75)
    print("Decision Gate Verdict Distribution:")
    for v in ["APPROVE", "REVIEW", "BLOCK"]:
        cnt = verdict_counts[v]
        print(f"  - {v:<10}: {cnt:,} ({cnt/total_processed*100:.1f}%)")
    print("-" * 75)
    print("CRITICAL FINANCIAL SAFETY METRICS:")
    print(f"  - UNSAFE APPROVAL RATE:   {unsafe_approval_rate:.2f}% ({unsafe_approved_count}/{total_unsafe_count} unsafe cases approved) [TARGET: 0.0%]")
    print(f"  - SAFE APPROVAL RATE:     {safe_approval_rate:.2f}% ({safe_approved_count}/{total_safe_count} safe cases approved)")
    print(f"  - REVIEW RATE:            {review_rate:.2f}% ({verdict_counts['REVIEW']}/{total_processed} cases routed to review)")
    print(f"  - BLOCK PRECISION:        {block_precision:.2f}% ({unsafe_blocked_count}/{verdict_counts['BLOCK']} blocked cases were unsafe)")
    print(f"  - DECISION ACCURACY:      {accuracy_pct:.2f}% ({correct_verdicts}/{total_processed} exact verdict matches)")
    print("-" * 75)
    print("FINANCIAL EXPOSURE ANALYSIS (Paise to INR):")
    print(f"  - Total Unsafe Potential Exposure:  INR {total_unsafe_exp_minor/100:,.2f}")
    print(f"  - Unsafe Exposure APPROVED:         INR {unsafe_approved_exp_minor/100:,.2f} ({unsafe_approved_exp_minor/max(1, total_unsafe_exp_minor)*100:.2f}%)")
    print(f"  - Unsafe Exposure BLOCKED:          INR {unsafe_blocked_exp_minor/100:,.2f} ({unsafe_blocked_exp_minor/max(1, total_unsafe_exp_minor)*100:.2f}%)")
    print(f"  - Unsafe Exposure REVIEWED:         INR {unsafe_reviewed_exp_minor/100:,.2f} ({unsafe_reviewed_exp_minor/max(1, total_unsafe_exp_minor)*100:.2f}%)")
    print("-" * 75)
    print("Matched Decision Rules Frequency:")
    for rule_id, cnt in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {rule_id:<12}: {cnt:,} ({cnt/total_processed*100:.1f}%)")
    print("-" * 75)
    print("Scenario Class Matrix (Class vs Decision Gate Verdict):")
    print(f"  {'Scenario Class':<18} | {'APPROVE':<8} | {'REVIEW':<8} | {'BLOCK':<8}")
    print("  " + "-" * 50)
    for s_cls in sorted(class_matrix.keys()):
        b = class_matrix[s_cls]
        print(f"  {s_cls:<18} | {b['APPROVE']:<8} | {b['REVIEW']:<8} | {b['BLOCK']:<8}")
    print("=" * 75)


if __name__ == "__main__":
    main()
