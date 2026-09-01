# TrustLedger — Ground-Truth Benchmark Specification

**Version:** 0.1.0 (Phase 2 Benchmark Engine)  
**Specification Status:** Ground-Truth Methodology Standard  

---

## 1. Benchmark Philosophy

The TrustLedger Benchmark Dataset is designed to evaluate financial decision verification systems with absolute empirical objectivity.

The core principle is:
> **Ground truth is established deterministically at data generation time, completely independent of any LLM or AI verification engine.**

The evaluation harness compares future system verdicts against hidden ground truth labels to measure precision, recall, false approval rates, and prevented financial exposure without circular model reasoning.

---

## 2. Benchmark Dataset Manifest

```json
{
  "dataset_version": "0.1.0",
  "contract_version": "trustledger.contract.v1",
  "random_seed": 20260829,
  "record_counts": {
    "decisions": 10000,
    "merchants": 25,
    "customers": 5000,
    "transactions": 12060,
    "orders": 12060,
    "evidence": 10240
  },
  "verdict_distribution": {
    "SAFE": 3538,
    "UNSAFE": 4345,
    "REVIEW_REQUIRED": 2117
  },
  "split_counts": {
    "train": 7000,
    "validation": 1500,
    "test": 1500
  }
}
```

---

## 3. Data Split Isolation Strategy

To prevent data contamination during model evaluation or rule tuning:
1. **Held-Out Test Set**: The `test.jsonl` split (1,500 decisions) is strictly held out. It must never be used for prompt engineering, rule tuning, or error analysis.
2. **Entity Isolation**: Related records (e.g. decision proposals referencing identical transactions or merchant policies) are grouped atomically within splits to prevent cross-split leakage.

---

## 4. Financial Exposure Metric

Every `UNSAFE` or `REVIEW_REQUIRED` decision in the hidden ground-truth dataset records a `financial_exposure_minor` amount representing potential monetary risk:
- **Excess Refund**: Difference between requested refund amount and original transaction value.
- **Policy Overage**: Total requested value exceeding merchant auto-approval threshold.
- **Duplicate Action**: Full duplicated transaction value.

This allows future evaluation suites to compute total monetary liability prevented by TrustLedger verification gates.
