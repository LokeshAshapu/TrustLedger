"""
TrustLedger Forensic Diagnostic Tool
Phase 3.1 Correction Pass
"""

import argparse
import json
import os
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
    parser = argparse.ArgumentParser(description="TrustLedger Forensic Diagnostic Script")
    parser.add_argument("--input", default="data/splits/test.jsonl", help="Path to input test split JSONL")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    args = parser.parse_args()

    processed_dir = os.path.join(args.data_dir, "processed")
    gt_dir = os.path.join(args.data_dir, "ground-truth")

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
    engine = DeterministicTrustEngine()
    test_decisions = load_jsonl_list(args.input)

    class_a_false_positives = []
    class_c_misses = []
    class_j_misses = []

    for req in test_decisions:
        d_id = req["decision_id"]
        res = engine.verify(req, context)
        gt = labels_db.get(d_id, {})
        cls = gt.get("scenario_class", "")

        if cls == "CLASS_A" and res.hard_failures:
            class_a_false_positives.append((req, res, gt))
        elif cls == "CLASS_C" and not res.hard_failures:
            class_c_misses.append((req, res, gt))
        elif cls == "CLASS_J" and not res.hard_failures:
            class_j_misses.append((req, res, gt))

    print("=" * 70)
    print("FORENSIC DIAGNOSTIC REPORT: Phase 3.1 Analysis")
    print("=" * 70)
    print(f"SAFE (CLASS_A) False HARD Positives Found: {len(class_a_false_positives)}")
    print(f"Duplicate Action (CLASS_C) Misses Found:   {len(class_c_misses)}")
    print(f"Contradictory Context (CLASS_J) Misses Found: {len(class_j_misses)}")
    print("=" * 70)

    # 1. Inspect CLASS_A False Positives
    print("\n--- SAMPLE CLASS_A (SAFE) FALSE POSITIVES ---")
    for req, res, gt in class_a_false_positives[:10]:
        print(f"\nDecision ID: {req['decision_id']} | Action: {req['action_type']} | Amount: INR {req['amount']['amount_minor']/100}")
        print(f"Merchant: {req['merchant_id']} | Customer: {req['customer_id']} | Txn: {req.get('transaction_id')}")
        print("Hard Failures:")
        for h in res.hard_failures:
            print(f"  - [{h.code}] {h.message}")
        txn = transactions_db.get(req.get("transaction_id", ""))
        if txn:
            print(f"Txn Details: Status={txn.get('status')}, Amount=INR {txn.get('amount', {}).get('amount_minor', 0)/100}, Order={txn.get('order_id')}")

    # 2. Inspect CLASS_C Misses
    print("\n--- SAMPLE CLASS_C (DUPLICATE ACTION) MISSES ---")
    for req, res, gt in class_c_misses[:10]:
        print(f"\nDecision ID: {req['decision_id']} | Action: {req['action_type']} | Txn: {req.get('transaction_id')}")
        print(f"Stated Reason: {req.get('reason')}")
        print(f"Evidence References: {req.get('evidence_references')}")
        for ref_id in req.get('evidence_references', []):
            ev = evidence_db.get(ref_id)
            if ev:
                print(f"  Evidence {ref_id}: Type={ev.get('evidence_type')}, SourceRec={ev.get('source_record_id')}, Status={ev.get('verification_status')}")

    # 3. Inspect CLASS_J Misses
    print("\n--- SAMPLE CLASS_J (CONTRADICTORY CONTEXT) MISSES ---")
    for req, res, gt in class_j_misses[:10]:
        print(f"\nDecision ID: {req['decision_id']} | Action: {req['action_type']} | Txn: {req.get('transaction_id')}")
        print(f"Reason: Category={req.get('reason', {}).get('category')}, Explanation={req.get('reason', {}).get('explanation')}")
        print(f"Evidence References: {req.get('evidence_references')}")
        for ref_id in req.get('evidence_references', []):
            ev = evidence_db.get(ref_id)
            if ev:
                print(f"  Evidence {ref_id}: Type={ev.get('evidence_type')}, SourceRec={ev.get('source_record_id')}")


if __name__ == "__main__":
    main()
