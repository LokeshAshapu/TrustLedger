# Trust Ledger — Trust Boundaries & Security Governance

**Version:** 0.1.0 (Phase 0 Foundation)  
**Security Classification:** Core Governance Specification  

---

## 1. Executive Summary

TrustLedger operates on a zero-trust model regarding autonomous AI agents. In traditional software architectures, services authenticated with API credentials are fully trusted to execute operations. In an AI agent environment, credential authenticity does **NOT** equal decision safety.

An AI agent may hold valid merchant credentials yet propose an unsafe, fraudulent, hallucinated, or policy-breaching financial action. TrustLedger separates **Proposal Authority** from **Execution Gate Authority**.

---

## 2. Trust Domains & System Boundaries

```
+-----------------------------------------------------------------------------------+
| UNTRUSTED DOMAIN                                                                  |
|                                                                                   |
|  +-------------------+                                                            |
|  |     AI Agent      |  Proposes Financial Actions (REFUND/DISCOUNT/RECOVERY/PAYOUT)|
|  |  (LLM / Bot / App) |  NO execution power, NO direct payment access             |
|  +-------------------+                                                            |
+-----------------------------------------------------------------------------------+
                                  |
                                  | POST /api/v1/decisions/verify (DecisionRequest)
                                  v
+-----------------------------------------------------------------------------------+
| TRUSTLEDGER SECURITY DOMAIN                                                       |
|                                                                                   |
|  +------------------+     +-------------------+     +--------------------------+  |
|  |  Evidence Engine | --> |   Policy Engine   | --> | AI Verification Engine   |  |
|  | (Hash & Proof)   |     | (Hard Constraints)|     | (Contextual Reasoning)   |  |
|  +------------------+     +-------------------+     +--------------------------+  |
|                                                                 |                 |
|                                                                 v                 |
|                                                     +--------------------------+  |
|                                                     |      Decision Gate       |  |
|                                                     | (APPROVE / REVIEW / BLK) |  |
|                                                     +--------------------------+  |
+-----------------------------------------------------------------------------------+
             |                                     |                                
   Verdict == APPROVE                     Verdict == REVIEW                         
             v                                     v                                
+---------------------------+       +-----------------------------------------------+
| PROTECTED FINANCIAL DOMAIN|       | HUMAN OVERSIGHT DOMAIN                        |
|                           |       |                                               |
| +-----------------------+ |       | +-------------------------------------------+ |
| | Financial Exec System | |       | | Human Review Queue                        | |
| | (Mock / Gateway API)  | |       | | (Approve / Reject Escalations)            | |
| +-----------------------+ |       | +-------------------------------------------+ |
+---------------------------+       +-----------------------------------------------+
```

---

## 3. Detailed Entity Matrix

| Entity | Role | Granted Permissions | Prohibited Actions | Trust Classification |
| :--- | :--- | :--- | :--- | :--- |
| **AI Agent** | Proposer | Submit `DecisionRequest` payloads to TrustLedger API. | Cannot execute payments, modify merchant policies, bypass verification, or access payment gateways directly. | **Untrusted** |
| **TrustLedger** | Verifier & Gatekeeper | Validate schema, verify evidence, evaluate policies, run risk checks, execute AI verifier, issue binding verdict. | Cannot originate financial actions independently; cannot ignore hard policy violations. | **Trusted Security Boundary** |
| **Human Reviewer** | Escalation Authority | Review `REVIEW` verdict queue, inspect evidence diffs, issue manual override `APPROVE` or `BLOCK`. | Cannot bypass cryptographic audit logging; cannot modify immutable historical traces. | **Trusted Human Authority** |
| **Financial System** | Executor | Execute financial movement **ONLY** upon receiving cryptographically signed `APPROVE` verdict token from TrustLedger. | Cannot accept direct execution calls from AI Agents or unverified callers. | **Protected Infrastructure** |

---

## 4. Non-Negotiable Invariants

### Invariant 1: No Direct Execution Route
> **AI Agent → Financial System direct routing is architecturally impossible.**  
> The financial execution endpoints (or mock execution services) reside within a protected network perimeter that rejects all ingress traffic except requests carrying a valid, signed TrustLedger `APPROVE` authorization token.

### Invariant 2: Deterministic Supremacy
> **The LLM cannot override a hard deterministic policy.**  
> If the Policy Engine identifies a hard safety constraint violation (e.g., amount exceeds cap, frequency limit reached, restricted currency), the system verdict is deterministically set to `BLOCK` (or `REVIEW` for soft rules). The AI Verifier's response cannot flip this outcome to `APPROVE`.

### Invariant 3: Fail-Closed Default
> **Any system exception, timeout, or ambiguity defaults to safe containment.**  
> If the AI Verification service times out, an evidence link cannot be resolved, or an internal database error occurs during evaluation, TrustLedger MUST NOT default to `APPROVE`. It defaults to `REVIEW` (or `BLOCK` if in high-risk scope).

### Invariant 4: Immutable Audit Trace
> **Every decision lifecycle step generates an unalterable audit record.**  
> Audit logs include exact request payloads, policy evaluation results, raw AI outputs, decision gate reasoning, and execution tokens. Records are append-only.

---

## 5. Threat Model & Mitigation Strategy

| Threat Scenario | Attack Vector | TrustLedger Defense Mechanism |
| :--- | :--- | :--- |
| **Prompt Injection** | Customer feeds adversarial prompt into support chat to force AI agent to request ₹100,000 refund. | 1. Policy Engine enforces max refund hard limit (e.g., ₹25,000).<br>2. AI Verifier runs isolated verification prompt using structured Pydantic parser.<br>3. Decision Gate blocks amount exceeding threshold regardless of LLM claim. |
| **Agent Hallucination** | AI agent misinterprets customer chat and requests payout without proof. | Evidence Engine verifies referenced evidence IDs. If evidence is missing or hash invalid, evidence score drops to 0. Verdict becomes `REVIEW` or `BLOCK`. |
| **Replay Attack** | Malicious actor re-submits a previously approved `DecisionRequest` payload. | Decision Gate checks `decision_id` idempotency registry in MongoDB. Duplicate requests return cached original verdict without re-execution. |
| **Privilege Escalation** | AI Agent attempts to modify policy thresholds via API. | Policy modification endpoints require multi-factor Human Admin authentication. AI Agent API keys lack policy write permissions. |
