"""
TrustLedger Synthetic World Generator Command CLI
Phase 2 Benchmark Dataset Pipeline
"""

import argparse
import json
import os
import random
from datetime import datetime, timezone
from typing import List, Dict, Any
import yaml

from data.generator.entities import SyntheticWorld
from data.generator.scenarios import ScenarioGenerator

CURRENT_CONTRACT_VERSION = "trustledger.contract.v1"


def main():
    parser = argparse.ArgumentParser(description="TrustLedger Synthetic World Generator")
    parser.add_argument("--config", default="data/generator/config.yaml", help="Path to config file")
    args = parser.parse_args()

    # 1. Load Configuration
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    seed = cfg["seed"]
    target_decisions = cfg["dataset"]["target_decisions"]
    num_merchants = cfg["dataset"]["merchants_count"]
    num_customers = cfg["dataset"]["customers_count"]
    time_window_days = cfg["dataset"]["time_window_days"]

    processed_dir = cfg["output_paths"]["processed_dir"]
    ground_truth_dir = cfg["output_paths"]["ground_truth_dir"]
    splits_dir = cfg["output_paths"]["splits_dir"]
    manifest_path = cfg["output_paths"]["manifest_path"]

    for d in [processed_dir, ground_truth_dir, splits_dir]:
        os.makedirs(d, exist_ok=True)

    # 2. Initialize Seeded RNG
    rng = random.Random(seed)
    base_time = datetime(2026, 8, 29, 12, 0, 0, tzinfo=timezone.utc)

    # 3. Generate World Entities
    world = SyntheticWorld(rng, base_time, time_window_days)
    world.generate_world(num_merchants, num_customers)

    # 4. Generate Decisions & Ground Truth based on Scenario Distribution
    scenario_gen = ScenarioGenerator(world, rng)

    class_sub_dist = cfg["class_sub_distribution"]
    diff_dist = cfg["difficulty_distribution"]

    decisions: List[Dict[str, Any]] = []
    ground_truth_labels: List[Dict[str, Any]] = []

    scenario_counts: Dict[str, int] = {k: 0 for k in class_sub_dist.keys()}
    verdict_counts: Dict[str, int] = {"SAFE": 0, "UNSAFE": 0, "REVIEW_REQUIRED": 0}
    diff_counts: Dict[str, int] = {"EASY": 0, "MEDIUM": 0, "HARD": 0}

    # Pre-determine scenario sequence for target decisions
    scenario_classes = list(class_sub_dist.keys())
    weights = [class_sub_dist[c] for c in scenario_classes]

    diff_levels = list(diff_dist.keys())
    diff_weights = [diff_dist[d] for d in diff_levels]

    for _ in range(target_decisions):
        chosen_class = rng.choices(scenario_classes, weights=weights, k=1)[0]
        chosen_diff = rng.choices(diff_levels, weights=diff_weights, k=1)[0]

        obs_payload, gt_record = scenario_gen.generate_case_for_class(chosen_class, chosen_diff)

        decisions.append(obs_payload)
        ground_truth_labels.append(gt_record)

        scenario_counts[chosen_class] += 1
        verdict_counts[gt_record["ground_truth_verdict"]] += 1
        diff_counts[chosen_diff] += 1

    # 5. Write Observable JSONL Files to data/processed/
    with open(os.path.join(processed_dir, "decisions.jsonl"), "w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d) + "\n")

    with open(os.path.join(processed_dir, "evidence.jsonl"), "w", encoding="utf-8") as f:
        for ev in world.evidence_records.values():
            f.write(json.dumps(ev) + "\n")

    with open(os.path.join(processed_dir, "transactions.jsonl"), "w", encoding="utf-8") as f:
        for txn in world.transactions.values():
            f.write(json.dumps(txn) + "\n")

    with open(os.path.join(processed_dir, "customers.jsonl"), "w", encoding="utf-8") as f:
        for cust in world.customers.values():
            f.write(json.dumps(cust) + "\n")

    with open(os.path.join(processed_dir, "orders.jsonl"), "w", encoding="utf-8") as f:
        for ord_item in world.orders.values():
            f.write(json.dumps(ord_item) + "\n")

    with open(os.path.join(processed_dir, "policies.jsonl"), "w", encoding="utf-8") as f:
        for pol in world.policy_profiles.values():
            snap = {
                "contract_version": CURRENT_CONTRACT_VERSION,
                "policy_id": pol.policy_profile_id,
                "merchant_id": pol.merchant_id,
                "action_type": "REFUND",
                "rules": pol.to_snapshot_rules(),
                "effective_from": pol.effective_from,
                "effective_until": None,
                "policy_version": pol.policy_version,
            }
            f.write(json.dumps(snap) + "\n")

    with open(os.path.join(processed_dir, "refunds.jsonl"), "w", encoding="utf-8") as f:
        for ref_rec in world.refund_records.values():
            f.write(json.dumps(ref_rec) + "\n")


    # 6. Write Hidden Ground Truth to data/ground-truth/labels.jsonl
    with open(os.path.join(ground_truth_dir, "labels.jsonl"), "w", encoding="utf-8") as f:
        for gt in ground_truth_labels:
            f.write(json.dumps(gt) + "\n")

    # 7. Create Train / Validation / Test Splits in data/splits/
    indices = list(range(len(decisions)))
    rng.shuffle(indices)

    train_ratio = cfg["splits"]["train"]
    val_ratio = cfg["splits"]["validation"]

    train_end = int(len(decisions) * train_ratio)
    val_end = train_end + int(len(decisions) * val_ratio)

    train_indices = indices[:train_end]
    val_indices = indices[train_end:val_end]
    test_indices = indices[val_end:]

    def write_split(file_name: str, idx_list: List[int]):
        path = os.path.join(splits_dir, file_name)
        with open(path, "w", encoding="utf-8") as f:
            for i in idx_list:
                f.write(json.dumps(decisions[i]) + "\n")

    write_split("train.jsonl", train_indices)
    write_split("val.jsonl", val_indices)
    write_split("test.jsonl", test_indices)

    # 8. Create Dataset Manifest
    manifest = {
        "dataset_version": "0.1.0",
        "contract_version": CURRENT_CONTRACT_VERSION,
        "random_seed": seed,
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "record_counts": {
            "decisions": len(decisions),
            "merchants": len(world.merchants),
            "customers": len(world.customers),
            "transactions": len(world.transactions),
            "orders": len(world.orders),
            "evidence": len(world.evidence_records),
        },
        "verdict_distribution": verdict_counts,
        "scenario_distribution": scenario_counts,
        "difficulty_distribution": diff_counts,
        "split_counts": {
            "train": len(train_indices),
            "validation": len(val_indices),
            "test": len(test_indices),
        },
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # 9. Print Concise Summary Report
    print("=" * 60)
    print("TrustLedger Benchmark Dataset Generation Complete")
    print("=" * 60)
    print(f"Seed: {seed}")
    print(f"Merchants: {len(world.merchants)}")
    print(f"Customers: {len(world.customers):,}")
    print(f"Transactions: {len(world.transactions):,}")
    print(f"Decisions Generated: {len(decisions):,}")
    print("-" * 60)
    print("Ground Truth Verdict Distribution:")
    for v, c in verdict_counts.items():
        print(f"  {v}: {c:,} ({c / len(decisions) * 100:.1f}%)")
    print("-" * 60)
    print("Dataset Splits:")
    print(f"  Train (70%): {len(train_indices):,}")
    print(f"  Validation (15%): {len(val_indices):,}")
    print(f"  Test (15%): {len(test_indices):,}")
    print("=" * 60)


if __name__ == "__main__":
    main()
