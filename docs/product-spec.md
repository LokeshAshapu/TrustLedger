# TrustLedger — Product Specification

**Version:** 0.1.0 (Phase 0 Foundation)  
**Product:** TrustLedger — The Financial AI Firewall  
**Tagline:** Verify before AI moves money.  

---

## 1. Product Thesis

TrustLedger is an independent verification and decision-gating layer that operates between autonomous AI agents and core financial systems.

As artificial intelligence agents transition from advisory tools to operational decision-makers, merchants and financial institutions face a fundamental trust gap. Autonomous agents can rapidly analyze context, but they lack deterministic guarantees against hallucination, prompt injection, policy drift, context misinterpretation, and runaway financial liability.

TrustLedger does **NOT** originate financial decisions. Instead, it acts as a non-bypassable financial security gatekeeper. It independently evaluates proposed financial actions using schema validation, evidence verification, policy enforcement, consistency checking, risk scoring, and structured AI verification before any financial movement is authorized.

```
+--------------+       +------------------+       +-------------------+       +------------------+
|  AI Agent    | ----> |   TrustLedger    | ----> |  Decision Gate    | ----> | Financial System |
| (Proposer)   |       |  (Verification)  |       | (APPROVE/REV/BLK) |       | (Execution Only) |
+--------------+       +------------------+       +-------------------+       +------------------+
       |                                                                               ^
       +---------------------------- X BYPASS BLOCKED X -------------------------------+
```

---

## 2. Core Problem

Autonomous AI agents are increasingly tasked with handling financial workflows, such as:
- Refunding dissatisfied customers
- Offering loyalty discounts or retention incentives
- Retrying or recovering failed payments
- Disbursing vendor or partner payouts

The core bottleneck preventing widespread adoption of financial AI agents is **trust and governance**.

The question facing modern fintech engineering is no longer simply:  
*"Can AI make the financial decision?"*

It is:  
**"Can we deterministically verify that the proposed decision deserves to be executed?"**

TrustLedger provides the defense-in-depth infrastructure required to answer that question with absolute auditability, safety, and precision.

---

## 3. MVP Scope & Supported Action Types

To maintain strict reliability and bounded safety, TrustLedger MVP supports **exactly four** financial action types:

1. **`REFUND`**: Returning funds to a customer for a previous transaction (partial or full).
2. **`DISCOUNT`**: Applying promotional, goodwill, or adjustment price reductions to an order/invoice.
3. **`PAYMENT_RECOVERY`**: Initiating a retry, plan adjustment, or charge attempt for a failed or past-due payment.
4. **`PAYOUT`**: Disbursing funds to an external merchant, vendor, driver, or affiliate account.

No additional action types are permitted in the MVP core engine.

### Canonical Action Context
Every proposed action submitted to TrustLedger must encapsulate:
- Proposed Action Type (`REFUND`, `DISCOUNT`, `PAYMENT_RECOVERY`, `PAYOUT`)
- Financial Amount & Currency
- Actor / Originating AI Agent Metadata
- Customer and/or Merchant Context
- Transaction & Order Context (when applicable)
- Stated Reason & Justification
- Evidence References (receipts, chat logs, policy links, delivery notes)
- Applicable Policy Context
- Verification Result & Verdict
- Execution Outcome (once authorized)
- Immutable Audit Trail

---

## 4. Verdict Model

TrustLedger produces one of exactly three outcomes for every decision request:

| Verdict | Meaning | Downstream Action |
| :--- | :--- | :--- |
| **`APPROVE`** | The proposed action is fully supported by valid evidence, satisfies all deterministic policies, passes consistency checks, and falls within acceptable risk thresholds. | Action authorized for automated financial execution. |
| **`REVIEW`** | The action may be legitimate, but evidence is incomplete, confidence is below automated threshold, or policy requires human confirmation. | Action routed to Human-in-the-Loop review queue. |
| **`BLOCK`** | The action violates a hard deterministic safety rule, contains contradictory evidence, exceeds financial boundaries, or presents unacceptable risk. | Action strictly rejected. Financial execution prohibited. |

> [!IMPORTANT]
> **No Forced Binary Verdicts**: TrustLedger explicitly forbids forcing ambiguous or uncertain cases into `APPROVE` or `BLOCK`. Uncertainty or incomplete proof must always map to `REVIEW`.

---

## 5. Non-Negotiable Safety Principle

**Deterministic safety mechanisms always have absolute authority over LLM outputs.**

The LLM is a reasoning assistant within TrustLedger, NOT the final authority.

```
Proposed AI Decision
        ↓
Schema Validator
        ↓
Evidence Engine
        ↓
Policy Engine (Deterministic Rules - ABSOLUTE AUTHORITY)
        ↓
Consistency Engine
        ↓
Risk Engine
        ↓
AI Verifier (Reasoning Assistant)
        ↓
Decision Gate
        ↓
APPROVE / REVIEW / BLOCK
```

### Safety Override Example
If a merchant policy specifies a maximum automated refund limit of **₹25,000**, and an AI agent submits a `REFUND` request of **₹40,000**:
- Even if the AI Verifier determines the customer's complaint is 100% genuine and well-reasoned, the deterministic Policy Engine rule produces a hard violation.
- The final verdict **MUST NOT** be `APPROVE`. It must be escalated to `REVIEW` (or `BLOCK` if over hard cap).
- The LLM can never override a deterministic rule.

---

## 6. AI Responsibility & Bounded Scope

The AI Verifier component within TrustLedger operates under strict behavioral constraints.

### Permitted AI Responsibilities
- Evaluating whether the proposed financial action logically follows from the attached evidence.
- Detecting subtle textual contradictions between customer claims, chat history, and stated reasons.
- Identifying missing context or missing evidence required for decision validation.
- Assessing contextual risk factors that deterministic keyword rules might miss.
- Recommending escalation reasons for human reviewers when context is ambiguous.

### Strictly Prohibited AI Actions
The AI Verifier must **NEVER**:
1. Execute financial transactions or call payment APIs.
2. Modify financial records or database states directly.
3. Override, bypass, or relax deterministic policies or threshold limits.
4. Modify safety thresholds or system rules.
5. Fabricate evidence or assume unverified facts.
6. Return unparsed natural language output where structured data is required.

---

## 7. Initial Data Models

### 7.1 DecisionRequest
```typescript
interface DecisionRequest {
  decision_id: string;              // UUID v4
  action_type: 'REFUND' | 'DISCOUNT' | 'PAYMENT_RECOVERY' | 'PAYOUT';
  agent_id: string;                 // Identifier of the originating AI Agent
  merchant_id: string;              // Merchant scope identifier
  customer_id: string;              // Customer scope identifier
  transaction_id?: string;          // Associated payment transaction ID
  order_id?: string;                // Associated order ID
  amount: number;                   // Positive numeric amount
  currency: string;                 // ISO 4217 code (e.g., INR, USD)
  reason: string;                   // Stated justification from AI agent
  evidence_references: string[];    // Array of Evidence IDs or URIs
  requested_at: string;             // ISO 8601 UTC timestamp
  metadata?: Record<string, any>;   // Additional contextual Key-Value pairs
}
```

### 7.2 Evidence
```typescript
interface Evidence {
  evidence_id: string;              // UUID v4
  evidence_type: 'CHAT_LOG' | 'DELIVERY_PROOF' | 'RECEIPT' | 'POLICY_DOC' | 'SUPPORT_TICKET' | 'SYSTEM_LOG';
  source: string;                   // System of origin (e.g., Zendesk, Shopify, Stripe)
  source_record_id: string;         // Unique ID in origin system
  timestamp: string;                // ISO 8601 UTC timestamp of creation
  content_hash: string;             // SHA-256 hash of evidence payload for tampering prevention
  reference_url?: string;           // Secure link to raw evidence artifact
  verification_status: 'UNVERIFIED' | 'VERIFIED_VALID' | 'FAILED_INTEGRITY' | 'EXPIRED';
}
```

### 7.3 Policy
```typescript
interface Policy {
  policy_id: string;
  merchant_id: string;
  action_type: 'REFUND' | 'DISCOUNT' | 'PAYMENT_RECOVERY' | 'PAYOUT';
  name: string;
  description: string;
  rule_type: 'MAX_AMOUNT' | 'COOLDOWN_PERIOD' | 'FREQUENCY_LIMIT' | 'REQUIRE_EVIDENCE' | 'ALLOWED_CURRENCIES';
  threshold: number | string | boolean;
  severity: 'HARD_BLOCK' | 'SOFT_REVIEW';
  effective_from: string;
  effective_until?: string;
  is_active: boolean;
}
```

### 7.4 VerificationResult
```typescript
interface VerificationResult {
  decision_id: string;
  deterministic_checks: {
    schema_valid: boolean;
    policy_passed: boolean;
    violations: Array<{ policy_id: string; rule: string; message: string }>;
  };
  evidence_score: number;            // Normalized 0.0 - 1.0 score
  consistency_result: {
    is_consistent: boolean;
    contradictions: string[];
  };
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  ai_verdict: 'APPROVE' | 'REVIEW' | 'BLOCK';
  ai_confidence: number;             // Normalized 0.0 - 1.0 float
  final_verdict: 'APPROVE' | 'REVIEW' | 'BLOCK';
  reasons: string[];
  missing_evidence: string[];
  verified_at: string;
}
```

### 7.5 ExecutionResult (Simulated in Phase 0)
```typescript
interface ExecutionResult {
  execution_id: string;
  decision_id: string;
  status: 'PENDING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';
  executed_at: string;
  amount: number;
  currency: string;
  provider_reference?: string;       // Simulated gateway reference (e.g., pay_sim_12345)
  error_code?: string;
  error_message?: string;
}
```

### 7.6 AuditRecord
```typescript
interface AuditRecord {
  event_id: string;                  // UUID v4
  decision_id: string;
  event_type: 'DECISION_REQUESTED' | 'EVIDENCE_EVALUATED' | 'POLICY_EVALUATED' | 'AI_VERIFIED' | 'VERDICT_ISSUED' | 'EXECUTION_SIMULATED' | 'HUMAN_OVERRIDDEN';
  actor: string;                     // Agent ID, System Engine ID, or Human User ID
  timestamp: string;                 // High-precision ISO 8601 UTC timestamp
  previous_state?: string;
  new_state: string;
  reason: string;
  metadata: Record<string, any>;
  signature?: string;                // Cryptographic payload signature
}
```

---

## 8. Security Principles

1. **Principle of Least Privilege**: AI agents possess proposal permissions only; zero access to financial keys or settlement APIs.
2. **Immutable Audit Events**: All state changes produce append-only audit records with cryptographic hashes.
3. **Explicit Action Authorization**: Actions must explicitly match approved merchant policy rules.
4. **Zero Direct LLM Execution Access**: The AI verifier output passes through the Decision Gate before hitting any execution engine.
5. **Deterministic Rule Supremacy**: Hard constraints cannot be bypassed by prompt injection or model hallucination.
6. **Input Validation**: All incoming requests are strictly validated against JSON Schemas before processing.
7. **Structured AI Outputs**: The AI engine uses strict Pydantic/JSON schemas for output parsing.
8. **Evidence Provenance**: Evidence artifacts require hash verification to prevent post-facto tampering.
9. **Idempotent Decision Gating**: Submitting the same `decision_id` twice returns cached verdict without re-execution.
10. **Fail-Closed Design**: Any system error, timeout, or unexpected exception defaults the verdict to `REVIEW` or `BLOCK`.
11. **Human Escalation Queue**: Unresolved ambiguous states map directly to `REVIEW` for human oversight.
12. **Secret Isolation**: Zero API keys or credentials stored in repository code; environment injection mandatory.

---

## 15. Evaluation Philosophy

TrustLedger will be evaluated on a held-out synthetic benchmark dataset containing realistic financial agent decision proposals (including valid requests, policy breaches, fraud attempts, adversarial prompt injections, and contradictory evidence cases).

Evaluation metrics will focus exclusively on empirically measured performance:
- **Unsafe Decision Recall**: Percentage of unsafe/fraudulent actions correctly caught (`REVIEW` or `BLOCK`).
- **Unsafe Decision Precision**: Percentage of flagged decisions that were genuinely unsafe.
- **False Approval Rate**: Frequency of policy-violating requests mistakenly marked `APPROVE` (Target: 0%).
- **False Block Rate**: Frequency of legitimate requests incorrectly blocked.
- **Evidence Accuracy**: Precision of evidence validation and contradiction detection.
- **Financial Exposure Prevented**: Total monetary value of blocked policy breaches.
- **Latency & Throughput**: End-to-end verification millisecond latency distribution.

*Zero placeholder benchmarks or synthetic claims ("95% accurate") will be included prior to empirical benchmark execution.*

---

## 16. Future UI Design Direction (Phase 2+)

*Note: UI implementation is out of scope for Phase 0.*

The future TrustLedger UI is envisioned as a **Financial AI Security Operating System**:
- **Aesthetic**: Deep dark slate environment with restrained futuristic accents, high information density, and precise monospace typography.
- **Visualizations**: Live decision flow telemetry, real-time risk gauges, interactive evidence graphs, policy breakdown trees, and audit state timelines.
- **Micro-interactions**: Luminous state transitions (`APPROVE` teal glow, `REVIEW` amber warning, `BLOCK` crimson alert), animated state machines, and high-clarity diff inspectors for human review.
