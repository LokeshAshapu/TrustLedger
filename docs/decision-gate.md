# TrustLedger — Signal Aggregation & Auditable Decision Gate Specification

**Gate Version:** `trustledger.decision-gate.v1`  
**Document Status:** Authoritative Decision Gate Specification  

---

## 1. Executive Summary & Core Principle

The **Decision Gate** is the authoritative, 100% deterministic decision layer of TrustLedger. It aggregates signals from contract validation, deterministic verification findings, financial risk assessments, and contextual AI reasoning to produce exactly one immutable verdict: **`APPROVE`**, **`REVIEW`**, or **`BLOCK`**.

> **Core Principle**: *"AI can propose. AI can reason. TrustLedger decides."* The AI verifier is advisory. Deterministic safety policies strictly override AI opinions. The Decision Gate contains ZERO LLM calls and uses explicit, auditable decision rules (`TL-DG-001` through `TL-DG-011`).

---

## 2. Authority Hierarchy

```
LEVEL 1 — CONTRACT SAFETY (Invalid JSON/Money/Identity)
   ↓ BLOCK
LEVEL 2 — HARD DETERMINISTIC SAFETY (Over-cap, Duplicate, Entity Mismatch)
   ↓ BLOCK (AI CANNOT OVERRIDE THIS)
LEVEL 3 — EXECUTION RISK (HIGH/CRITICAL Exposure Risk)
   ↓ REVIEW
LEVEL 4 — EVIDENCE UNCERTAINTY (Missing/Conflicting Artifacts)
   ↓ REVIEW
LEVEL 5 — AI CONTEXTUAL REASONING (SUPPORT / UNCERTAIN / CONTRADICT)
   ↓ APPROVE / REVIEW
```

---

## 3. Decision Matrix & Decision Rules

| Rule ID | Deterministic Status | Risk Level | Evidence State | AI Recommendation | Verdict | Primary Reason Code |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`TL-DG-001`** | Contract Invalid | Any | Any | Any | **`BLOCK`** | `CONTRACT_INVALID` |
| **`TL-DG-002`** | HARD Failure | Any | Any | Any (incl. SUPPORT) | **`BLOCK`** | Primary HARD Finding Code |
| **`TL-DG-003`** | PASS | Any | Insufficient | Any | **`REVIEW`** | `EVIDENCE_MISSING` |
| **`TL-DG-004`** | PASS | Any | Conflicting | Any | **`REVIEW`** | `EVIDENCE_CONFLICTING` |
| **`TL-DG-005`** | PASS | CRITICAL | Any | Any | **`REVIEW`** | `CRITICAL_FINANCIAL_RISK` |
| **`TL-DG-006`** | PASS | HIGH | Any | Any | **`REVIEW`** | `HIGH_FINANCIAL_RISK` |
| **`TL-DG-007`** | PASS | Any | Any | CONTRADICT | **`REVIEW`** | `AI_CONTEXTUAL_CONTRADICTION` |
| **`TL-DG-008`** | PASS | Any | Any | UNCERTAIN | **`REVIEW`** | `AI_CONTEXTUAL_UNCERTAINTY` |
| **`TL-DG-009`** | PASS | Any | Any | AI_UNAVAILABLE | **`REVIEW`** | `AI_VERIFIER_UNAVAILABLE` |
| **`TL-DG-010`** | PASS | LOW / MEDIUM | Sufficient | SUPPORT | **`APPROVE`** | `ALL_SAFETY_CHECKS_PASSED` |
| **`TL-DG-011`** | PASS | LOW | Sufficient | Skipped / None | **`APPROVE`** | `LOW_RISK_CLEAN_PASS` |

---

## 4. Cryptographic Hashing (SHA-256)

Every `DecisionResult` includes an immutable 64-character hex `decision_hash` computed via SHA-256 over the canonical JSON payload (with volatile timestamps stripped). This guarantees strict idempotency and auditability.
