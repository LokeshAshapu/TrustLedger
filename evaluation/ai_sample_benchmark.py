"""
TrustLedger AI Contextual Verifier Sample Benchmark & Diagnostic CLI
Phase 5 AI Contextual Verification Layer
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
    parser = argparse.ArgumentParser(description="TrustLedger AI Sample Benchmark Diagnostic Tool")
    parser.add_argument("--input", default="data/splits/test.jsonl", help="Input test split file")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    parser.add_argument("--sample-size", type=int, default=30, help="Number of representative cases to sample")
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

    labels_db = load_jsonl_map(os.path.join(gt_dir, "labels.jsonl"), "decision_id")

    # Select representative sample across classes
    all_decisions = load_jsonl_list(args.input)
    class_buckets: Dict[str, List[Dict[str, Any]]] = {}
    for d in all_decisions:
        gt = labels_db.get(d["decision_id"], {})
        s_class = gt.get("scenario_class", "CLASS_UNKNOWN")
        if s_class not in class_buckets:
            class_buckets[s_class] = []
        class_buckets[s_class].append(d)

    sample_decisions = []
    items_per_class = max(1, args.sample_size // max(1, len(class_buckets)))
    for s_class in sorted(class_buckets.keys()):
        sample_decisions.extend(class_buckets[s_class][:items_per_class])

    sample_decisions = sample_decisions[:args.sample_size]

    det_engine = DeterministicTrustEngine()
    risk_engine = FinancialRiskEngine()

    # Determine Provider (Use NVIDIA if key is in env, else Mock Provider)
    if os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY"):
        try:
            ai_service = AIVerificationService(NVIDIAProvider())
        except Exception:
            ai_service = AIVerificationService(MockLLMProvider())
    else:
        ai_service = AIVerificationService(MockLLMProvider())

    rec_counts = {"SUPPORT": 0, "UNCERTAIN": 0, "CONTRADICT": 0, "AI_UNAVAILABLE": 0}
    latencies = []
    citation_valid_count = 0
    total_citations = 0

    class_rec_breakdown: Dict[str, Dict[str, int]] = {}
    hard_ai_align_count = 0
    uncertain_ai_clarify_count = 0

    print("=" * 75)
    print("TrustLedger AI Verification Engine Sample Benchmark Report (Phase 5)")
    print("=" * 75)
    print(f"Provider Active:  {ai_service.provider.__class__.__name__}")
    print(f"Sample Size:      {len(sample_decisions)} cases")
    print("-" * 75)

    for req in sample_decisions:
        d_id = req["decision_id"]
        gt = labels_db.get(d_id, {})
        s_class = gt.get("scenario_class", "CLASS_UNKNOWN")

        det_res = det_engine.verify(req, context)
        risk_res = risk_engine.assess(req, context, det_res)

        # Build Packet (Strict Ground-Truth Isolation)
        packet = AIVerificationPacketBuilder.build(req, context, det_res, risk_res)

        start_t = time.time()
        ai_res = ai_service.verify_context(packet)
        lat_ms = (time.time() - start_t) * 1000
        latencies.append(lat_ms)

        rec = ai_res.recommendation.value
        rec_counts[rec] = rec_counts.get(rec, 0) + 1

        if s_class not in class_rec_breakdown:
            class_rec_breakdown[s_class] = {"SUPPORT": 0, "UNCERTAIN": 0, "CONTRADICT": 0}
        if rec in class_rec_breakdown[s_class]:
            class_rec_breakdown[s_class][rec] += 1

        # Check citation validity
        valid_evs = {e["evidence_id"] for e in packet.relevant_evidence}
        for cited in ai_res.supporting_evidence:
            total_citations += 1
            if cited in valid_evs:
                citation_valid_count += 1

        # AI Value Alignment Checks
        if det_res.hard_failures and rec == "CONTRADICT":
            hard_ai_align_count += 1
        elif det_res.warnings and rec == "UNCERTAIN":
            uncertain_ai_clarify_count += 1

    citation_rate = (citation_valid_count / total_citations * 100) if total_citations > 0 else 100.0

    print("AI Recommendation Distribution:")
    for r, cnt in rec_counts.items():
        print(f"  - {r:<15}: {cnt} ({cnt/len(sample_decisions)*100:.1f}%)")
    print("-" * 75)
    print("Performance & Citation Metrics:")
    print(f"  - Average Latency:      {statistics.mean(latencies):.2f} ms")
    print(f"  - Median Latency:       {statistics.median(latencies):.2f} ms")
    print(f"  - Citation Accuracy:    {citation_rate:.1f}% ({citation_valid_count}/{total_citations} valid evidence citations)")
    print("-" * 75)
    print("Recommendations Breakdown by Scenario Class:")
    print(f"  {'Scenario Class':<18} | {'SUPPORT':<8} | {'UNCERTAIN':<10} | {'CONTRADICT':<10}")
    print("  " + "-" * 55)
    for s_cls in sorted(class_rec_breakdown.keys()):
        b = class_rec_breakdown[s_cls]
        print(f"  {s_cls:<18} | {b['SUPPORT']:<8} | {b['UNCERTAIN']:<10} | {b['CONTRADICT']:<10}")
    print("-" * 75)
    print("AI Value Matrix vs Deterministic Engine:")
    print(f"  - HARD Violation Acknowledgment Alignment: {hard_ai_align_count} cases")
    print(f"  - Warning Contextual Clarification Value:   {uncertain_ai_clarify_count} cases")
    print("=" * 75)


if __name__ == "__main__":
    main()
