# TrustLedger — Canonical Financial Decision Contracts

**Contract Version:** `trustledger.contract.v1`  
**Document Status:** Standardized Machine-Readable Specification  

---

## 1. Overview & Single Semantic Source of Truth

TrustLedger enforces a strict architectural principle: **There is exactly ONE canonical semantic contract definition across all system components.**

Whether a request originates from an AI Agent, passes through the Node.js API Gateway, undergoes policy check evaluation, is processed by the Python FastAPI AI Verifier, or is recorded in the Audit Database, all components consume and emit the same canonical data structures.

External adapters may map agent-specific payloads into the canonical contract, but internal verification logic relies exclusively on `trustledger.contract.v1`.

---

## 2. Shared Vocabulary & Core Enums

### 2.1 Supported Action Types (`ActionType`)
TrustLedger MVP supports **exactly four** financial action types:

- **`REFUND`**: Returning payment to a customer for a previous transaction.
- **`DISCOUNT`**: Applying a fixed price reduction or percentage discount to an order or invoice.
- **`PAYMENT_RECOVERY`**: Initiating a retry or mandate recovery attempt for a past-due/failed payment.
- **`PAYOUT`**: Disbursing funds to an external merchant, vendor, or driver settlement account.

### 2.2 Verdict Outcomes (`VerdictType`)
- **`APPROVE`**: Fully backed by valid evidence, satisfies all deterministic rules, passes consistency checks, and falls within risk thresholds. Authorized for execution.
- **`REVIEW`**: Legitimate potential, but evidence is incomplete, confidence is below automated threshold, or policy requires human confirmation. Routed to Human-in-the-Loop review queue.
- **`BLOCK`**: Violates a hard deterministic safety rule, contains contradictory evidence, exceeds financial boundaries, or presents unacceptable risk. Execution strictly forbidden.

### 2.3 Decision Lifecycle States (`LifecycleState`)
- `RECEIVED` → `NORMALIZED` → `EVIDENCE_CHECK` → `POLICY_CHECK` → `CONSISTENCY_CHECK` → `RISK_ASSESSMENT` → `AI_VERIFICATION` → `VERDICT`
- Downstream States: `READY_FOR_EXECUTION` | `HUMAN_REVIEW` | `BLOCKED` | `EXECUTING` | `EXECUTED` | `FAILED`

---

## 3. Safe Monetary Representation (`Money`)

To eliminate floating-point precision errors (e.g. `0.1 + 0.2 = 0.30000000000000004`), TrustLedger represents money exclusively using **integer minor units**.

```typescript
interface Money {
  amount_minor: number; // Integer minor units (e.g., Paise for INR, Cents for USD)
  currency: string;     // ISO 4217 uppercase currency code (e.g., INR)
}
```

### Examples
- **₹1,499.00** → `{ "amount_minor": 149900, "currency": "INR" }`
- **₹0.00** → `{ "amount_minor": 0, "currency": "INR" }`
- **₹10,000.50** → `{ "amount_minor": 1000050, "currency": "INR" }`

### Validation Invariants
- `amount_minor` must be an integer (floating-point numbers are strictly rejected).
- `amount_minor` must be `>= 0` (negative amounts are rejected).
- `currency` must be a 3-letter uppercase ISO code (e.g., `INR`).

---

## 4. Core Canonical Contracts

### 4.1 DecisionRequest
```typescript
interface DecisionRequest {
  contract_version: "trustledger.contract.v1";
  decision_id: string;
  action_type: ActionType;
  agent_id: string;
  merchant_id: string;
  customer_id?: string | null;
  transaction_id?: string | null;
  order_id?: string | null;
  amount: Money;
  discount_spec?: DiscountSpec | null;
  reason: {
    category: ReasonCategory;
    explanation?: string;
  };
  evidence_references: string[]; // Array of unique Evidence IDs
  requested_at: string;          // ISO-8601 UTC string
  metadata?: Record<string, unknown> | null;
}
```

#### Action-Specific Validation Requirements
- **`REFUND`**: `customer_id`, `transaction_id`, `amount`, and `reason` are **MANDATORY**.
- **`DISCOUNT`**: Requires at least `customer_id` OR `order_id`. Must specify valid `amount` or `discount_spec` (fixed amount or percentage points `0.01` to `100.0`).
- **`PAYMENT_RECOVERY`**: `customer_id`, `transaction_id`, `amount`, and `reason` are **MANDATORY**.
- **`PAYOUT`**: `merchant_id`, `amount`, and `reason` are **MANDATORY**. `customer_id` is NOT required.

---

### 4.2 Evidence Artifact & Provenance
```typescript
interface Evidence {
  contract_version: "trustledger.contract.v1";
  evidence_id: string;
  evidence_type: EvidenceType;
  source: string;              // System of origin (e.g., Zendesk, Shopify, Stripe)
  source_record_id: string;    // Record ID in origin system
  timestamp: string;           // Provenance creation timestamp (ISO 8601)
  content_hash?: string | null; // Cryptographic SHA-256 hash if available
  verification_status: EvidenceVerificationStatus;
  metadata?: Record<string, unknown> | null;
}
```

---

### 4.3 Versioned PolicySnapshot
```typescript
interface PolicySnapshot {
  contract_version: "trustledger.contract.v1";
  policy_id: string;
  merchant_id: string;
  action_type: ActionType;
  rules: Array<{
    rule_id: string;
    rule_name: string;
    description?: string;
    threshold_value?: number | string | boolean | null;
    is_hard_constraint: boolean;
  }>;
  effective_from: string;
  effective_until?: string | null;
  policy_version: string; // e.g. "v2.1.0" for reproducible auditing
}
```

---

### 4.4 VerificationResult (Deterministic vs. AI Signals)
The `VerificationResult` explicitly decouples deterministic rule evaluation from AI contextual reasoning outputs to guarantee absolute auditability.

```typescript
interface VerificationResult {
  contract_version: "trustledger.contract.v1";
  decision_id: string;
  verdict: VerdictType;          // APPROVE | REVIEW | BLOCK
  confidence: number;           // Normalized 0.0 - 1.0 confidence signal
  risk_level: RiskLevel;        // LOW | MEDIUM | HIGH | CRITICAL
  evidence_result: {
    evidence_score: number;
    verified_count: number;
    missing_references: string[];
  };
  policy_result: {
    passed: boolean;
    violations: Array<{ policy_id: string; rule_id: string; message: string }>;
  };
  consistency_result: {
    is_consistent: boolean;
    contradictions: string[];
  };
  ai_result: {
    verdict_recommendation: VerdictType;
    reasoning_summary: string;
    detected_risk_factors: string[];
    confidence: number;
  };
  reasons: string[];
  missing_evidence: string[];
  verification_started_at: string;
  verification_completed_at: string;
  verifier_version: string;
}
```

> [!NOTE]
> **Confidence Signal Note**: `confidence` is a normalized system confidence metric (0.0 to 1.0), NOT an absolute guarantee of factual truth.

---

### 4.5 ExecutionResult & AuditRecord
- **`ExecutionResult`**: Tracks execution simulation attempts, gateway idempotency keys, provider references, and error codes.
- **`AuditRecord`**: Captures state transition traces with `actor_type` (`AI_AGENT`, `TRUSTLEDGER`, `HUMAN`, `FINANCIAL_SYSTEM`), previous/new states, timestamps, and correlation IDs.

---

## 5. Machine-Readable JSON Schemas

Official JSON Schemas matching TypeScript interfaces 1:1 are located under `schemas/json/`:
- `schemas/json/decision-request.schema.json`
- `schemas/json/evidence.schema.json`
- `schemas/json/policy-snapshot.schema.json`
- `schemas/json/verification-result.schema.json`
- `schemas/json/execution-result.schema.json`
- `schemas/json/audit-record.schema.json`

---

## 6. Python Interoperability Strategy

The Python AI Verifier service imports Pydantic v2 models directly from `verifier/contracts.py`:
```python
from verifier.contracts import DecisionRequest, VerificationResult, VerdictType
```
This strategy guarantees that Python models maintain exact parity with TypeScript contracts without schema duplication drift.
