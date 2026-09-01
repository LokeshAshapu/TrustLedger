import json

with open("evaluation/reports/phase8-baseline.json") as f1, open("evaluation/reports/full-evaluation.json") as f2:
    b = json.load(f1)
    h = json.load(f2)

bm = b["metrics"]
hm = h["metrics"]
bs = bm["safety_metrics"]
hs = hm["safety_metrics"]

print("=== BEFORE / AFTER PHASE 8.1 METRICS COMPARISON ===")
print(f"Overall Accuracy:    Baseline={bm['overall_accuracy_pct']}% -> Hardened={hm['overall_accuracy_pct']}%")
print(f"Macro F1 Score:      Baseline={bm['macro_f1_pct']}% -> Hardened={hm['macro_f1_pct']}%")
print(f"Unsafe Approval:     Baseline={bs['unsafe_approval_rate_pct']}% -> Hardened={hs['unsafe_approval_rate_pct']}%")
print(f"Safe Approval Rate:  Baseline={bs['safe_approval_rate_pct']}% -> Hardened={hs['safe_approval_rate_pct']}%")
print(f"Review Rate:         Baseline={bs['review_rate_pct']}% -> Hardened={hs['review_rate_pct']}%")
print(f"Review Precision:    Baseline={bs['review_precision_pct']}% -> Hardened={hs['review_precision_pct']}%")
print(f"Review Recall:       Baseline={bs['review_recall_pct']}% -> Hardened={hs['review_recall_pct']}%")
print(f"Block Precision:     Baseline={bs['block_precision_pct']}% -> Hardened={hs['block_precision_pct']}%")
print(f"Block Recall:        Baseline={bs['block_recall_pct']}% -> Hardened={hs['block_recall_pct']}%")
print("-" * 60)
print("=== CLASS_H METRICS ===")
print("Baseline Class H:", json.dumps(b['scenario_metrics']['CLASS_H'], indent=2))
print("Hardened Class H:", json.dumps(h['scenario_metrics']['CLASS_H'], indent=2))
