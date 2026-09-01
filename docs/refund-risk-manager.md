# TrustLedger — AI Refund Risk Manager

> **RAZORPAY AI BUILDATHON • AI RISK MANAGER TRACK SPECIALIZATION**  
> *Verify an AI-proposed refund before money moves. AI can recommend. TrustLedger decides.*

---

## 1. Problem Overview

Autonomous AI agents are increasingly entrusted with customer support and refund processing. However, granting an LLM agent direct API access to initiate merchant refunds creates catastrophic financial exposure:
1. **Prompt Injection & Adversarial Exploitation**: Customers can manipulate agent context to demand unauthorized refunds.
2. **Policy Cap Breaches**: AI agents frequently miss or miscalculate merchant auto-refund limits (e.g. approving a ₹60,000 refund against a ₹25,000 policy cap).
3. **Stale or Conflicting Evidence**: AI agents accept outdated attachments (>30 days old) or ignore evidence signal mismatches (e.g. Courier API showing package delivered vs Customer Support ticket claiming non-delivery).
4. **Duplicate Refund Replays**: AI agents lack deterministic memory of active or previously processed refund transactions.

**TrustLedger** solves this problem by acting as an authoritative, non-bypassable verification and authorization layer between AI agent intent and financial execution systems.

---

## 2. Core Architectural Principle

```text
AI Agent / LLM
      ↓ (Proposes Refund)
TrustLedger REST API (POST /api/v1/decisions/verify)
      ↓
Contract Validation
      ↓
Evidence Provenance & Freshness Audit
      ↓
Deterministic Verification (Level 1)
      ↓
Policy Engine (Level 2 Hard Caps)
      ↓
Financial Risk Engine (Refund Risk Taxonomy)
      ↓
NVIDIA AI Contextual Verification (Advisory)
      ↓
Authoritative Decision Gate
      ↓
┌──────────────────────────────────────────────┐
│ APPROVE → ExecutionAuthorization Issued       │
│ REVIEW  → Execution Blocked (Human Review)   │
│ BLOCK   → Execution Blocked (No Token)       │
└──────────────────────────────────────────────┘
```

---

## 3. Dedicated Refund Risk Taxonomy

| Risk Taxonomy Code | Severity | Expected Verdict | Trigger Condition & Description |
| :--- | :---: | :---: | :--- |
| `POLICY_CAP_VIOLATION` | **HARD** | **BLOCK** | Refund requested exceeds merchant's automatic refund limit (e.g. ₹60,000 vs ₹25,000 cap). |
| `DUPLICATE_REFUND` | **HARD** | **BLOCK** | A refund has already been issued or an equivalent refund action is recorded. |
| `REFUND_AMOUNT_MISMATCH` | **HARD** | **BLOCK** | Requested refund exceeds the original transaction or refundable balance. |
| `ENTITY_MISMATCH` | **HARD** | **BLOCK** | Customer ID, order ID, or transaction ID relationship does not match authoritative records. |
| `NONEXISTENT_TRANSACTION` | **HARD** | **BLOCK** | Referenced transaction ID cannot be verified in repository. |
| `MISSING_EVIDENCE` | **WARNING** | **REVIEW** | Required supporting evidence artifact is absent. |
| `CONFLICTING_EVIDENCE` | **WARNING** | **REVIEW** | Two trusted evidence sources disagree (e.g. Courier API vs Support Log). |
| `STALE_EVIDENCE` | **WARNING** | **REVIEW** | Evidence timestamp exceeds freshness threshold (>30 days old). |
| `REFUND_VELOCITY_RISK` | **WARNING** | **REVIEW** | Unusually high customer refund frequency within recent window. |

---

## 4. Key Financial Safety Metrics & Evaluation Evidence

Verified against **1,500 held-out evaluation test cases**:

- **Overall Decision Accuracy**: `95.73%` (1,436 / 1,500 exact verdict matches)
- **Unsafe Approval Rate**: `0.00%` (0 of 637 unsafe cases approved)
- **Unsafe Exposure Approved**: `₹0.00`
- **Unsafe Potential Exposure Blocked**: `₹97,74,478.00` (100.00% of unsafe exposure blocked)
- **Block Recall**: `100.00%` (637 / 637 unsafe cases blocked)
- **Security Suite**: `10 / 10 (100.0%)` adversarial attack vectors prevented
- **Safe False-Block Rate**: `6.02%` (33 / 548 safe cases conservatively gated to prevent risk)

---

## 5. Signature Demo Scenario: AI SUPPORT vs Policy Cap Breach

```text
┌─────────────────────────────────────────────────────────────┐
│ PROPOSED REFUND ACTION                                       │
│ Action: REFUND ₹60,000 (Order #ord_100)                      │
│ Merchant Policy Limit: ₹25,000                               │
│ Cap Violation: +₹35,000 Over Cap                             │
├─────────────────────────────────────────────────────────────┤
│ AI ADVISORY CONTEXT (NVIDIA LLM)                             │
│ Recommendation: SUPPORT (0.99 Confidence)                   │
├─────────────────────────────────────────────────────────────┤
│ TRUSTLEDGER AUTHORITATIVE VERDICT                            │
│ Verdict: BLOCK                                              │
│ Rule: TL-DG-002 (Hard Policy Breach)                        │
│ Banner: AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY     │
├─────────────────────────────────────────────────────────────┤
│ EXECUTION AUTHORIZATION                                      │
│ Status: ⛔ NO FINANCIAL EXECUTION AUTHORIZED                 │
└─────────────────────────────────────────────────────────────┘
```
