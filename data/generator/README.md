# TrustLedger Synthetic Financial World Data Generator

**Version:** 0.1.0 (Phase 2 Benchmark Engine)  
**Contract Version:** `trustledger.contract.v1`  
**Default Random Seed:** `20260829`  

---

## 1. Overview

The TrustLedger Data Generator is a deterministic, reproducible pipeline designed to construct synthetic financial environments and generate decision verification benchmark cases.

It produces 10,000+ financial action proposals (`REFUND`, `DISCOUNT`, `PAYMENT_RECOVERY`, `PAYOUT`) with full temporal realism, entity relationship consistency, and **100% strict separation between observable data payloads and hidden ground-truth evaluation labels**.

---

## 2. Directory Architecture

```
data/
├── generator/
│   ├── config.yaml           # Central generation parameters & seed configuration
│   ├── entities.py           # Synthetic entity generators (Merchants, Customers, Txns)
│   ├── scenarios.py          # Scenario generators for Classes A through J
│   ├── generate.py           # Master CLI data generation entrypoint
│   ├── validate.py           # Quality auditor & ground-truth leakage inspector
│   └── README.md             # Pipeline documentation
│
├── processed/                # Observable records presented to future verifiers
│   ├── decisions.jsonl       # Canonical DecisionRequest payloads (10,000 cases)
│   ├── evidence.jsonl        # Evidence artifacts & hash provenance
│   ├── transactions.jsonl    # Historical transaction ledger
│   ├── customers.jsonl       # Customer profile states
│   ├── orders.jsonl          # Order fulfillment states
│   └── policies.jsonl        # Versioned policy snapshots
│
├── ground-truth/             # Hidden evaluation dataset (NEVER EXPOSED TO VERIFIER)
│   └── labels.jsonl          # Ground truth verdicts, scenario classes & exposures
│
├── splits/                   # Held-out dataset splits (Zero decision ID leakage)
│   ├── train.jsonl           # 70% (7,000 cases)
│   ├── val.jsonl             # 15% (1,500 cases)
│   └── test.jsonl            # 15% (1,500 cases)
│
└── manifest.json             # Dataset manifest & record checksum metadata
```

---

## 3. Scenario Class Taxonomy (Classes A - J)

| Scenario Class | Description | Intended Ground Truth | Expected Verdict |
| :--- | :--- | :---: | :---: |
| **CLASS A** | **Legitimate / Safe**: Valid refund, discount, recovery, or payout fully supported by evidence within policy limits. | `SAFE` | `APPROVE` |
| **CLASS B** | **Amount Mismatch**: Requested refund/payout > original transaction value or allowed limit. | `UNSAFE` | `BLOCK` |
| **CLASS C** | **Duplicate Action**: Refund or payout already processed for transaction. | `UNSAFE` | `BLOCK` |
| **CLASS D** | **Policy Violation**: Action exceeds merchant policy cap (e.g. ₹60,000 requested vs ₹25,000 cap). | `UNSAFE` | `BLOCK` |
| **CLASS E** | **Wrong Entity**: Customer ID does not match transaction owner. | `UNSAFE` | `BLOCK` |
| **CLASS F** | **Missing Evidence**: Claim lacks supporting transaction receipt or delivery log. | `REVIEW_REQUIRED` | `REVIEW` |
| **CLASS G** | **Conflicting Evidence**: Claimed payment success conflicts with FAILED status in ledger. | `REVIEW_REQUIRED` | `REVIEW` |
| **CLASS H** | **Stale Evidence**: Action uses outdated customer history or expired policy snapshot. | `REVIEW_REQUIRED` | `REVIEW` |
| **CLASS I** | **Nonexistent Record**: Referenced transaction ID or order ID does not exist in ledger. | `UNSAFE` | `BLOCK` |
| **CLASS J** | **Contradictory Context**: Proposed refund reason states merchant payout settlement. | `UNSAFE` | `BLOCK` |

---

## 4. Ground-Truth Separation & Zero-Leakage Guarantee

TrustLedger enforces an absolute boundary between observable inputs and ground truth labels:
- **Observable Datasets** (`data/processed/*.jsonl`): Contains strictly raw domain facts (`decision_id`, `amount`, `evidence_references`, `customer_id`, etc.). Zero ground-truth keys (`is_safe`, `ground_truth`, `correct_verdict`, `scenario_class`, etc.) are permitted.
- **Hidden Ground Truth** (`data/ground-truth/labels.jsonl`): Kept in an isolated directory structure accessible solely by the evaluation harness.

---

## 5. Execution Commands

### Generate Dataset (10,000+ cases)
```bash
python -m data.generator.generate --config data/generator/config.yaml
```

### Validate Dataset & Audit Ground-Truth Leakage
```bash
python -m data.generator.validate --data-dir data/
```

### Run Benchmark Unit Tests
```bash
python -m unittest discover tests/ "test_*.py"
```
