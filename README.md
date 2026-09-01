# TrustLedger — AI Refund Risk Manager
## Financial AI Firewall & Verification Platform

> **Primary Statement**: Verify an AI-proposed refund before money moves.  
> **Core Thesis**: AI can recommend. TrustLedger decides.

[![Evaluation Truth](https://img.shields.io/badge/Decision_Accuracy-95.73%25-emerald?style=for-the-badge&logo=shield)](file:///c:/Users/ASUS/Downloads/trustledger/docs/phase8-1-safety-hardening.md)
[![Unsafe Approval Rate](https://img.shields.io/badge/Unsafe_Approval_Rate-0.00%25-blue?style=for-the-badge&logo=security)](file:///c:/Users/ASUS/Downloads/trustledger/docs/evaluation-safety.md)
[![Unsafe Exposure Blocked](https://img.shields.io/badge/Unsafe_Exposure_Blocked-₹97.74_Lakh_(100%25)-purple?style=for-the-badge)](file:///c:/Users/ASUS/Downloads/trustledger/docs/evaluation-safety.md)
[![Adversarial Vectors Passed](https://img.shields.io/badge/Adversarial_Suite-10%2F10_PASS-green?style=for-the-badge)](file:///c:/Users/ASUS/Downloads/trustledger/evaluation/adversarial_suite.py)

---

## 1. Executive Summary

**TrustLedger — AI Refund Risk Manager** is an authoritative financial verification and authorization layer positioned between autonomous customer service AI agents and real financial payment gateways (such as **Razorpay**).

As customer support and fintech automation increasingly delegate refund recommendations to autonomous LLM agents, companies face severe financial exposure from **hallucinated refunds**, **policy cap breaches**, **duplicate refund requests**, **evidence staleness**, and **prompt injection attacks**.

TrustLedger solves this critical vulnerability by enforcing a strict **Non-Bypass Authorization Boundary**:

```text
Autonomous AI Agent (Proposes Refund)
                ↓
    TrustLedger Decision Gate
 (Deterministic Rules + Risk Engine + AI Verifier)
                ↓
    DecisionResult & ExecutionAuthorization
  (APPROVE → ISSUED | REVIEW / BLOCK → NONE)
                ↓
    ExecutionGateway & RazorpayTestClient
 (Executes POST /v1/payments/:id/refund ONLY IF AUTHORIZED)
```

---

## 2. Buildathon E2E Demo Harness (1-Line CLI Demo)

Execute the official judge demonstration harness in terminal output:

```bash
python -m evaluation.buildathon_demo
```

Runs 3 canonical scenarios using the real production pipeline:
- **Scenario A (SAFE REFUND)**: ₹1,500 refund $\rightarrow$ `APPROVE` (`TL-DG-010`), `ExecutionAuthorization` ISSUED, Razorpay READY.
- **Scenario B (HUMAN REVIEW)**: ₹500 refund with stale evidence (>30 days) $\rightarrow$ `REVIEW` (`TL-DG-003`), `Authorization` NONE, 0 Razorpay calls.
- **Scenario C (SIGNATURE SAFETY ATTACK)**: ₹60,000 refund vs ₹25,000 policy cap, AI SUPPORT (0.99) $\rightarrow$ `BLOCK` (`TL-DG-002`), `Authorization` NONE, 0 Razorpay calls. Displays: **`!!! AI DID NOT OVERRIDE SAFETY POLICY !!!`**.

---

## 3. Core Architecture & Verification Engine

TrustLedger operates a 5-tier verification stack:

1. **Canonical Schema & Contract Normalizer**: Validates incoming decision requests using strict Pydantic models with integer minor units (paise) to prevent floating-point precision loss.
2. **Deterministic Trust Engine**: Evaluates strict merchant policy caps (e.g. max ₹25,000 refund), evidence presence, and timestamp staleness ($> 30$ days $\rightarrow$ `STALE_EVIDENCE`).
3. **Financial Risk Engine**: Scores exposure across 9 refund risk taxonomy codes (`POLICY_CAP_VIOLATION`, `DUPLICATE_REFUND`, `REFUND_AMOUNT_MISMATCH`, `ENTITY_MISMATCH`, `NONEXISTENT_TRANSACTION`, `MISSING_EVIDENCE`, `CONFLICTING_EVIDENCE`, `STALE_EVIDENCE`, `REFUND_VELOCITY_RISK`).
4. **Contextual AI Verifier**: Powered by NVIDIA AI (`meta/llama-3.1-70b-instruct`) with fail-safe fallback to `REVIEW` if API is degraded or missing.
5. **Authoritative Decision Gate**: Renders unalterable verdicts (`APPROVE`, `REVIEW`, `BLOCK`). **Deterministic policy rules override AI recommendations under all circumstances.**

---

## 4. Measured Evaluation Truth

Evaluated on **1,500 held-out test cases** with 100% ground-truth isolation:

- **Baseline Decision Accuracy**: **95.73%** (1,436 / 1,500 test cases correct)
- **Unsafe Approval Rate**: **0.00%** (0 / 1,500 unsafe approvals)
- **Unsafe Financial Exposure Blocked**: **₹97,74,478.00 (100.00%)**
- **Safe Approval Rate**: **93.98%** (575 / 612 valid requests approved)
- **Adversarial Security Suite**: **10 / 10 Vectors Passed** (prompt injection, citation spoofing, replay attacks, hash tampering, amount tampering)
- **Financial Invariants**: **9 / 9 Verified**

---

## 5. Razorpay Integration & Test Mode Validation

TrustLedger features a production-quality server-side Razorpay Test-Mode integration:

- **Client Package**: `execution/razorpay_client.py` executing `POST /v1/payments/:id/refund`.
- **Environment Safeguard**: Strictly locked to `RAZORPAY_ENVIRONMENT=test`. Refuses live/production execution.
- **Server-Side Credentials**: `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` remain strictly on the server. Zero credential exposure in frontend code or API responses.
- **Idempotency & Retries**: Passes `X-Refund-Idempotency` header and performs bounded retries (max 2 attempts) for 5xx/network errors.
- **Opt-In E2E Validation**: `tests/test_razorpay_e2e.py` enables live network validation against real Razorpay Test Mode API when `RUN_RAZORPAY_E2E=true`.

---

## 6. Phased Development Roadmap

- [x] **Phase 0: Foundation & Specifications**
- [x] **Phase 1: Canonical Financial Decision Contract**
- [x] **Phase 2: Synthetic Financial World & Ground-Truth Benchmark**
- [x] **Phase 3: Deterministic Trust Engine**
- [x] **Phase 4: Financial Risk & Exposure Scoring Engine**
- [x] **Phase 5: Contextual AI Verifier**
- [x] **Phase 6: Decision Gate & Signal Aggregator**
- [x] **Phase 7: Bounded Financial Execution Simulator**
- [x] **Phase 8: Full Evaluation, Safety Validation & Adversarial Testing**
- [x] **Phase 8.1: Safety Hardening & Review Calibration**
- [x] **Phase 9A-9D: Security OS Frontend Control Plane**
- [x] **Phase 10A-10D: Real Backend Integration, NVIDIA AI & Evaluation Truth**
- [x] **Phase 11A: AI Refund Risk Manager Specialization**
- [x] **Phase 11B.1: Razorpay Test-Mode Refund Client**
- [x] **Phase 11B.2: ExecutionGateway Razorpay Integration**
- [x] **Phase 11B.3: Real Razorpay Test-Mode End-to-End Validation**
- [x] **Phase 11C.1: Buildathon E2E Demo Harness**
- [x] **Phase 11C.2: TrustLedger Final Security & Safety Audit**

---

## 7. Documentation Quick Links

- 📘 [Product Specification](file:///c:/Users/ASUS/Downloads/trustledger/docs/product-spec.md)
- 🔒 [Final Security & Safety Audit Report](file:///c:/Users/ASUS/Downloads/trustledger/docs/security-audit.md)
- 🎬 [Buildathon E2E Demo Guide](file:///c:/Users/ASUS/Downloads/trustledger/docs/buildathon-demo.md)
- 💳 [Razorpay Test-Mode E2E Guide](file:///c:/Users/ASUS/Downloads/trustledger/docs/razorpay-e2e.md)
- 🛡️ [AI Refund Risk Manager Spec](file:///c:/Users/ASUS/Downloads/trustledger/docs/refund-risk-manager.md)
- 🚀 [Hackathon Judge Quickstart](file:///c:/Users/ASUS/Downloads/trustledger/QUICKSTART.md)
- 🎥 [Video Presentation Script](file:///c:/Users/ASUS/Downloads/trustledger/docs/demo-script.md)
