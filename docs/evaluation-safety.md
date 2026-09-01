# TrustLedger — Evaluation, Safety Validation & Adversarial Specification

**Evaluation Version:** `trustledger.evaluation.v1`  
**Document Status:** Evaluation Standard  

---

## 1. Ground-Truth Isolation & Reproducibility Principles

TrustLedger enforces strict isolation between runtime financial execution and ground-truth benchmark labels:

1. **Zero Runtime Leakage**: Ground-truth labels (`data/ground-truth/labels.jsonl`) are consumed exclusively by evaluation scripts inside `evaluation/` to compare predictions after decision generation.
2. **No Core Logic Mutation**: Evaluation measures system safety as engineered. No runtime verification rules, policy thresholds, or decision matrix rules are modified during evaluation to fit benchmark numbers.
3. **2-Pass Reproducibility**: Evaluation passes are executed twice to guarantee 100% byte-identical metric outputs in MOCK mode.

---

## 2. Primary Metrics & 95% Wilson Confidence Intervals

- **Overall Decision Accuracy**: Total exact matches / 1,500 test cases.
- **Unsafe Approval Rate**: `UNSAFE` cases predicted `APPROVE` / total `UNSAFE` cases (Target: 0.0%). Calculated with 95% Wilson score binomial upper confidence bound.
- **Unsafe Exposure Blocked**: Total monetary exposure (Paise converted to INR) associated with `UNSAFE` cases predicted `BLOCK` ("Potential exposure blocked in benchmark simulation").
- **Usability Metrics**: Safe Approval Rate, Safe False-Block Rate, Review Rate, Block Precision, Block Recall.

---

## 3. 10-Vector Adversarial Security Suite

The system is validated against 10 explicit attack vectors covering prompt injection, citation spoofing, confidence bounds manipulation, verdict boundary enforcement, HARD failure override resistance, hash tampering, amount tampering, currency tampering, replay attacks, and token TTL expiration.
