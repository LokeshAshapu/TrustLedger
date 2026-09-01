# TrustLedger — Deterministic Trust Engine Specification

**Engine Version:** `trustledger.deterministic.v1`  
**Document Status:** Deterministic Verification Standard  

---

## 1. Executive Summary & Core Principle

The **Deterministic Trust Engine** is the non-bypassable, rule-based verification backbone of TrustLedger. It evaluates proposed financial decisions (`REFUND`, `DISCOUNT`, `PAYMENT_RECOVERY`, `PAYOUT`) against canonical contracts, evidence provenance, versioned merchant policy snapshots, and multi-record consistency rules **without calling an LLM or using non-deterministic models**.

> **Core Invariant**: Deterministic safety rules have absolute veto authority. Hard safety violations cannot be overridden by downstream LLMs or probabilistic models.

---

## 2. Deterministic Verification Architecture

```
+-----------------------------------------------------------------------------------+
| DETERMINISTIC TRUST ENGINE (trustledger.deterministic.v1)                          |
|                                                                                   |
|  +---------------------+      +--------------------+      +--------------------+  |
|  | Schema Validator    | ---> | Evidence Validator | ---> | Policy Engine      |  |
|  | (Phase 1 Pydantic)  |      | (Hash & Linkage)   |      | (PolicySnapshots)  |  |
|  +---------------------+      +--------------------+      +--------------------+  |
|                                                                     |             |
|                                                                     v             |
|                                                           +--------------------+  |
|                                                           | Consistency Engine |  |
|                                                           | (Multi-Record)     |  |
|                                                           +--------------------+  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| DeterministicVerificationResult                                                   |
| - schema_result, evidence_result, policy_result, consistency_result               |
| - findings: List[Finding] (HARD, WARNING, INFO)                                   |
| - potential_exposure: Money (Derived from observable DecisionRequest.amount)      |
| - NO FINAL APPROVE/REVIEW/BLOCK VERDICT (Gate deferred to Phase 4)                |
+-----------------------------------------------------------------------------------+
```

---

## 3. Finding Model & Severity Taxonomy

### Finding Model
```json
{
  "check_id": "POLICY_REFUND_AUTOMATED_CAP",
  "category": "POLICY",
  "severity": "HARD",
  "status": "FAIL",
  "code": "REFUND_LIMIT_EXCEEDED",
  "message": "Requested refund of ₹60,000.00 exceeds merchant's automated refund cap of ₹25,000.00.",
  "evidence_ids": ["ev_000301"],
  "details": {
    "requested_amount_minor": 6000000,
    "cap_minor": 2500000
  }
}
```

### Severity Levels
- **`HARD`**: Objective, non-negotiable rule violation (e.g. refund > transaction amount, refund > merchant policy cap, missing referenced transaction, wrong customer). Unsafe for automated execution.
- **`WARNING`**: Potential anomaly or incomplete information requiring further verification (e.g. unverified evidence status, missing non-critical artifact, conflicting delivery logs).
- **`INFO`**: Confirmation of successful rule verification.

---

## 4. Derived Potential Financial Exposure

The engine calculates observable financial exposure directly from the decision request:
```typescript
potential_exposure = MoneyAmount(
  amount_minor = request.amount.amount_minor,
  currency = request.amount.currency
)
```
*Note: `potential_exposure` is derived strictly from observable request data and does NOT read hidden ground-truth labels.*
