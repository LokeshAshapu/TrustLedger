# TrustLedger — System Architecture

**Version:** 0.1.0 (Phase 0 Foundation)  
**Document Status:** Approved Architecture Blueprint  

---

## 1. Architectural Overview

TrustLedger is designed as a modular, event-audited verification framework. It intercepts proposed financial decisions from autonomous AI agents, processes them through deterministic and probabilistic verification pipelines, and enforces a decision gate before any action can touch financial infrastructure.

```mermaid
flowchart TD
    subgraph AI_AGENT_ZONE["Untrusted AI Agent Domain"]
        A[AI Agent / LLM Worker]
    end

    subgraph TRUSTLEDGER_BOUNDARY["TrustLedger Security Boundary"]
        B[Decision API Endpoint]
        C[Decision Normalizer]
        
        subgraph VERIFICATION_PIPELINE["Verification Pipeline"]
            D[Evidence Engine]
            E[Policy Engine\n(Deterministic Rules)]
            F[Consistency Engine]
            G[Risk Engine]
            H[AI Verification Engine\n(Contextual Reasoning)]
        end
        
        I[Decision Gate\n(Signal Aggregator)]
        J{Verdict?}
        K[APPROVE]
        L[REVIEW]
        M[BLOCK]
        
        N[(Audit Layer / Ledger)]
    end

    subgraph EXECUTION_ZONE["Protected Financial Domain"]
        O[Simulated Execution Layer\n(Mock Gateway)]
        P[Human Review Queue]
    end

    %% Flow connections
    A -->|POST /api/v1/decisions/verify| B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    
    J -->|Approved| K
    J -->|Needs Proof/Borderline| L
    J -->|Hard Violation| M
    
    K --> O
    L --> P
    M -->|Halt| N
    
    B -.->|Log Request| N
    E -.->|Log Violations| N
    H -.->|Log AI Reasoning| N
    J -.->|Log Final Verdict| N
    O -.->|Log Execution State| N

    %% Explicit Blocked Direct Access Boundary
    A -.-X|STRICTLY BLOCKED: Direct Payment Access Forbidden| O

    %% Styling
    classDef target fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef gate fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef approve fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#f8fafc;
    classDef review fill:#451a03,stroke:#fbbf24,stroke-width:2px,color:#f8fafc;
    classDef block fill:#4c0519,stroke:#f87171,stroke-width:2px,color:#f8fafc;
    classDef audit fill:#312e81,stroke:#a5b4fc,stroke-width:1px,color:#f8fafc;

    class B,C,D,E,F,G,H target;
    class I gate;
    class K approve;
    class L review;
    class M block;
    class N audit;
```

---

## 2. Logical Components

### A. Decision API
- **Purpose**: Ingress gateway receiving HTTP `POST` decision verification payloads from AI agents.
- **Responsibilities**: Authentication, token verification, rate limiting, and request payload schema validation.

### B. Decision Normalizer
- **Purpose**: Converts incoming raw payloads from diverse agent formats into the canonical `DecisionRequest` model.
- **Responsibilities**: Field sanitization, timestamp standardization (ISO 8601 UTC), currency normalization, and ID tagging.

### C. Evidence Engine
- **Purpose**: Fetches, validates, and evaluates evidence artifacts associated with the proposed decision.
- **Responsibilities**: Checks evidence availability, verifies cryptographic content hashes (`SHA-256`), validates source credibility (e.g., Zendesk, Shopify, Stripe), and flags missing proof.

### D. Policy Engine (Deterministic Authority)
- **Purpose**: Executes hard business and safety rules specified by the merchant.
- **Responsibilities**: Checks monetary thresholds (e.g., max automated refund ₹25,000), checks customer frequency caps (e.g., max 2 refunds per customer per 30 days), enforces currency constraints, and evaluates cooldown periods.
- **Rule**: *Has absolute veto power over the verdict. If a hard policy fails, the decision CANNOT be APPROVED.*

### E. Consistency Engine
- **Purpose**: Cross-references decision elements to uncover logical or historical contradictions.
- **Responsibilities**: Compares requested refund amount vs original transaction amount, checks if order has already been refunded/cancelled, validates customer ID alignment across chat logs and order receipts.

### F. Risk Engine
- **Purpose**: Calculates financial exposure and contextual risk scoring.
- **Responsibilities**: Computes risk velocity scores, merchant risk caps, customer lifetime value ratio, and action severity.

### G. AI Verification Engine
- **Purpose**: Conducts deep contextual reasoning on unstructured evidence (chat logs, support tickets, reason texts).
- **Responsibilities**: Analyzes whether customer claims logically support the requested action, flags prompt injection or social engineering patterns, assigns confidence scores, and generates structured explanations.
- **Rule**: *Decoupled LLM provider interface (supports Gemini, OpenAI, Claude, or local models via standard interface).*

### H. Decision Gate
- **Purpose**: Aggregates signals from all verification engines to issue the final binding verdict (`APPROVE`, `REVIEW`, `BLOCK`).
- **Responsibilities**: Applies non-negotiable decision logic:
  - If Policy Engine violation == `TRUE` → Verdict = `BLOCK` (or `REVIEW` if soft policy)
  - If Consistency Engine contradiction == `TRUE` → Verdict = `BLOCK`
  - If Evidence score < threshold OR AI confidence < threshold → Verdict = `REVIEW`
  - If All checks pass → Verdict = `APPROVE`

### I. Execution Layer (Simulated in Phase 0)
- **Purpose**: Receives authorized (`APPROVE`) decisions and simulates financial execution.
- **Responsibilities**: Generates simulated gateway references (e.g., `pay_sim_99812`), returns idempotency tokens, and records execution status.
- **Rule**: *Never accessible by AI Agents directly. Only invoked by TrustLedger Decision Gate.*

### J. Audit Layer
- **Purpose**: Records immutable, append-only traces for every decision lifecycle step.
- **Responsibilities**: Captures request payloads, evidence hashes, policy evaluation logs, AI reasoning outputs, final verdicts, and simulated execution outcomes.

---

## 3. Technology Stack & Decoupled Architecture

| Component | Framework / Tech | Rationale |
| :--- | :--- | :--- |
| **Backend & API Gateway** | Node.js + Express + TypeScript | Fast async I/O, strong typing, clean interface definitions |
| **AI Verification Engine** | Python + FastAPI + Pydantic | Native AI/LLM ecosystem integration, structured schema validation |
| **Evaluation & Benchmark** | Python + pandas + scikit-learn | Rigorous data analysis, confusion matrix evaluation, metric reporting |
| **Database** | MongoDB | Document flexibility for structured evidence, policies, and audit events |
| **Frontend UI (Phase 2+)** | React + Vite + TypeScript | Modern, high-performance UI shell |

### LLM Decoupling Interface
The AI Verifier engine defines an abstract provider adapter:
```python
class LLMVerifierAdapter(ABC):
    @abstractmethod
    async def verify(self, packet: VerificationPacket) -> AIVerdictOutput:
        pass
```
This guarantees that switching underlying LLM providers (e.g., Google Gemini 3.6, OpenAI, Anthropic, or local open-weights models) requires zero code changes to TrustLedger's core decision engine.

---

## 4. Primary API Contract

### Request: `POST /api/v1/decisions/verify`

```json
{
  "decision_id": "dec_8f7b2a9c-1234-4567-89ab-cdef01234567",
  "action_type": "REFUND",
  "agent_id": "agent_support_bot_01",
  "merchant_id": "merch_razorpay_demo",
  "customer_id": "cust_99812",
  "transaction_id": "txn_pay_772182",
  "order_id": "ord_55412",
  "amount": 4500.00,
  "currency": "INR",
  "reason": "Customer reported received item damaged in transit. Attached photos and chat log.",
  "evidence_references": [
    "ev_chat_1122",
    "ev_img_3344"
  ],
  "requested_at": "2026-08-29T19:30:00Z"
}
```

### Response: `200 OK` (VerificationResult)

```json
{
  "decision_id": "dec_8f7b2a9c-1234-4567-89ab-cdef01234567",
  "deterministic_checks": {
    "schema_valid": true,
    "policy_passed": true,
    "violations": []
  },
  "evidence_score": 0.95,
  "consistency_result": {
    "is_consistent": true,
    "contradictions": []
  },
  "risk_level": "LOW",
  "ai_verdict": "APPROVE",
  "ai_confidence": 0.98,
  "final_verdict": "APPROVE",
  "reasons": [
    "Deterministically satisfies merchant auto-refund limit of ₹25,000.",
    "Valid damage photos and chat logs verified in evidence engine.",
    "Requested refund amount matches original transaction value."
  ],
  "missing_evidence": [],
  "verified_at": "2026-08-29T19:30:01.120Z"
}
```
