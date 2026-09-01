"""
TrustLedger Benchmark Dataset Validator & Leakage Inspector
Phase 2 Benchmark Dataset Pipeline
"""

import argparse
import json
import os
import sys
from typing import Dict, Set, List, Any

# Import Python compatibility contracts from verifier/contracts.py
from verifier.contracts import DecisionRequest

FORBIDDEN_GROUND_TRUTH_KEYS = {
    "ground_truth",
    "correct_verdict",
    "scenario_label",
    "is_safe",
    "is_fraud",
    "expected_verdict",
    "expected_action",
    "ground_truth_verdict",
    "expected_safe_action",
    "financial_exposure_minor",
    "scenario_class",
    "difficulty",
}


def scan_obj_for_leakage(obj: Any, file_name: str, line_no: int) -> List[str]:
    leaks = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_GROUND_TRUTH_KEYS:
                leaks.append(f"Forbidden ground-truth key '{k}' found in {file_name}:{line_no}")
            leaks.extend(scan_obj_for_leakage(v, file_name, line_no))
    elif isinstance(obj, list):
        for item in obj:
            leaks.extend(scan_obj_for_leakage(item, file_name, line_no))
    return leaks


def main():
    parser = argparse.ArgumentParser(description="TrustLedger Dataset Validator")
    parser.add_argument("--data-dir", default="data", help="Root data directory")
    args = parser.parse_args()

    processed_dir = os.path.join(args.data_dir, "processed")
    ground_truth_dir = os.path.join(args.data_dir, "ground-truth")
    splits_dir = os.path.join(args.data_dir, "splits")
    manifest_path = os.path.join(args.data_dir, "manifest.json")

    print("=" * 60)
    print("Running TrustLedger Data Quality & Ground-Truth Leakage Audit")
    print("=" * 60)

    # 1. Verify Manifest Existence
    if not os.path.exists(manifest_path):
        print(f"FAILED: Manifest file missing at {manifest_path}")
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"Manifest Version: {manifest.get('dataset_version')} | Seed: {manifest.get('random_seed')}")

    # 2. Check Ground-Truth Leakage in Observable Processed Files
    observable_files = ["decisions.jsonl", "evidence.jsonl", "transactions.jsonl", "customers.jsonl", "orders.jsonl", "policies.jsonl"]
    total_leakages = []

    for fn in observable_files:
        fp = os.path.join(processed_dir, fn)
        if not os.path.exists(fp):
            print(f"FAILED: Observable file missing: {fp}")
            sys.exit(1)

        with open(fp, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                total_leakages.extend(scan_obj_for_leakage(record, fn, line_no))

    if total_leakages:
        print("CRITICAL SECURITY FAILURE: Ground-truth leakage detected in observable data!")
        for leak in total_leakages[:10]:
            print(f"  - {leak}")
        sys.exit(1)

    print("PASSED: Zero ground-truth leakage detected in observable files.")

    # 3. Validate Phase 1 Canonical Contract Compliance
    decisions_path = os.path.join(processed_dir, "decisions.jsonl")
    decision_ids: Set[str] = set()
    contract_failures = 0

    with open(decisions_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            d_id = payload.get("decision_id")
            if d_id in decision_ids:
                print(f"FAILED: Duplicate decision_id '{d_id}' found in decisions.jsonl:{line_no}")
                sys.exit(1)
            decision_ids.add(d_id)

            try:
                DecisionRequest.model_validate(payload)
            except Exception as e:
                print(f"FAILED: Contract validation failed for decision {d_id}: {e}")
                contract_failures += 1

    if contract_failures > 0:
        print(f"FAILED: {contract_failures} DecisionRequests failed canonical contract validation.")
        sys.exit(1)

    print(f"PASSED: {len(decision_ids):,} DecisionRequests passed Phase 1 Pydantic contract validation.")

    # 4. Check Ground Truth Referential Alignment
    labels_path = os.path.join(ground_truth_dir, "labels.jsonl")
    label_decision_ids: Set[str] = set()

    with open(labels_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            d_id = record.get("decision_id")
            if d_id in label_decision_ids:
                print(f"FAILED: Duplicate ground-truth decision_id '{d_id}' found in labels.jsonl:{line_no}")
                sys.exit(1)
            label_decision_ids.add(d_id)

    if decision_ids != label_decision_ids:
        print(f"FAILED: Decision ID mismatch between decisions ({len(decision_ids)}) and labels ({len(label_decision_ids)})")
        sys.exit(1)

    print("PASSED: 100% referential alignment between decision requests and hidden ground-truth labels.")

    # 5. Check Split Isolation
    train_path = os.path.join(splits_dir, "train.jsonl")
    val_path = os.path.join(splits_dir, "val.jsonl")
    test_path = os.path.join(splits_dir, "test.jsonl")

    def get_split_ids(file_path: str) -> Set[str]:
        s_ids = set()
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    s_ids.add(rec["decision_id"])
        return s_ids

    train_ids = get_split_ids(train_path)
    val_ids = get_split_ids(val_path)
    test_ids = get_split_ids(test_path)

    if train_ids.intersection(val_ids) or train_ids.intersection(test_ids) or val_ids.intersection(test_ids):
        print("FAILED: Decision overlap detected between dataset splits!")
        sys.exit(1)

    print(f"PASSED: Split integrity confirmed (Train: {len(train_ids):,}, Val: {len(val_ids):,}, Test: {len(test_ids):,}). Zero overlap.")
    print("=" * 60)
    print("ALL DATASET QUALITY & SAFETY CHECKS PASSED CLEANLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
