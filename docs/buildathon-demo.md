# TrustLedger — Buildathon End-to-End Demo Harness

> **Core Principle**:  
> **AI CAN RECOMMEND. TRUSTLEDGER DECIDES.**  
> **ONLY AUTHORIZED APPROVE DECISIONS MAY REACH RAZORPAY.**

---

## Overview

The **Buildathon End-to-End Demo Harness** (`evaluation/buildathon_demo.py`) provides an offline, deterministic, judge-friendly demonstration of the complete TrustLedger financial AI firewall pipeline.

It proves that TrustLedger's **DecisionGate is the sole authoritative gatekeeper** for financial execution. Autonomous AI agents can recommend refund decisions, but deterministic policy safety rules, risk scoring, and evidence verification override AI recommendations whenever policy caps or evidence thresholds are breached.

---

## Architecture & Component Reuse

The harness connects the real production components already implemented in the TrustLedger repository:

```text
DecisionRequest
       ↓
Schema Validation (Canonical Phase 1 Contract)
       ↓
SyntheticDataRepository (Ground-truth isolated data)
       ↓
DeterministicTrustEngine (Schema, Evidence, Policy, Consistency)
       ↓
FinancialRiskEngine (Exposure & Taxonomy scoring)
       ↓
AIVerificationService (Contextual LLM Verifier)
       ↓
DecisionGate (Authoritative Signal Aggregator)
       ↓
ExecutionGateway (Non-Bypass Authorization Boundary)
       ↓
RazorpayTestClient (POST /v1/payments/:id/refund)
```

No second decision engine, fake authorization logic, or rule bypasses exist.

---

## Demonstration Scenarios

### 1. Scenario A — SAFE REFUND
- **Input**: Action = `REFUND`, Amount = ₹1,500 (`150000` paise), Evidence = Verified `ev_001`, Merchant Cap = ₹25,000.
- **Decision Gate**: Renders `APPROVE` via Rule `TL-DG-010`.
- **Authorization**: `ExecutionAuthorization` issued with status `ISSUED`.
- **Razorpay Status**: Execution `READY` (0 network calls made by default).

### 2. Scenario B — HUMAN REVIEW (STALE EVIDENCE)
- **Input**: Action = `REFUND`, Amount = ₹500 (`50000` paise), Evidence = `ev_stale_999` (timestamp > 30 days old).
- **Decision Gate**: Renders `REVIEW` via Rule `TL-DG-003`.
- **Authorization**: `None` (Zero authorization generated).
- **Razorpay Status**: `0` Razorpay calls. Force execution attempt returns `DENIED`.

### 3. Scenario C — SIGNATURE SAFETY ATTACK
- **Input**: Action = `REFUND`, Amount = ₹60,000 (`6000000` paise), Merchant Policy Cap = ₹25,000 (`2500000` paise), AI Signal = `SUPPORT` (confidence 0.99).
- **Deterministic Check**: `POLICY_CAP_VIOLATION` hard finding.
- **Decision Gate**: Renders `BLOCK` via Rule `TL-DG-002`.
- **Authorization**: `None` (Zero authorization generated).
- **Razorpay Status**: `0` Razorpay calls.
- **Key Display**: `!!! AI DID NOT OVERRIDE SAFETY POLICY !!!`

---

## How to Run

### Command

```bash
python -m evaluation.buildathon_demo
```

### Expected Output

```text
============================================================
       TRUSTLEDGER -- AI REFUND RISK MANAGER         
       BUILDATHON E2E DEMONSTRATION                 
============================================================

[1/3] SAFE REFUND
------------------------------------------------------------
Requested Amount:       INR 1,500.00
AI Signal:              SUPPORT
Risk Level:             LOW
TrustLedger Verdict:    APPROVE
Decision Rule:          TL-DG-010
Authorization:          ISSUED
Razorpay Execution:     READY

[+] SAFE PATH VERIFIED

[2/3] STALE EVIDENCE
------------------------------------------------------------
Requested Amount:       INR 500.00
Evidence:               STALE (>30 days)
AI Signal:              UNCERTAIN
TrustLedger Verdict:    REVIEW
Decision Rule:          TL-DG-003
Authorization:          NONE
Razorpay Calls:         0

[+] HUMAN REVIEW BOUNDARY VERIFIED

[3/3] SIGNATURE SAFETY ATTACK
------------------------------------------------------------
Requested Amount:       INR 60,000.00
Merchant Policy Cap:    INR 25,000.00
AI Signal:              SUPPORT (0.99)
Hard Finding:           POLICY_CAP_VIOLATION

TrustLedger Verdict:    BLOCK
Decision Rule:          TL-DG-002
Authorization:          NONE
Razorpay Calls:         0

!!! AI DID NOT OVERRIDE SAFETY POLICY !!!

[+] FINANCIAL SAFETY BOUNDARY VERIFIED

============================================================
                    SAFETY SUMMARY                          
============================================================
Unsafe approvals:             0
Unsafe exposure approved:     INR 0.00
Hard-rule bypasses:           0
Razorpay calls on BLOCK:      0
Razorpay calls on REVIEW:     0

                    DEMO PASSED                             
============================================================
```

---

## Safe Offline Demo vs Real Razorpay E2E

| Feature | `buildathon_demo.py` (Default Demo) | `test_razorpay_e2e.py` (Live E2E) |
| :--- | :--- | :--- |
| **Purpose** | Offline Buildathon judge presentation | Live Razorpay API network validation |
| **Credentials Required** | **NO** (Zero credentials needed) | **YES** (`RAZORPAY_KEY_ID`, `KEY_SECRET`) |
| **Opt-In Flag** | None (Runs offline safely) | `RUN_RAZORPAY_E2E=true` |
| **Razorpay Network Calls** | **0** (Offline simulation boundary) | Real Test-Mode API refund execution |
| **Exit Code** | `0` on success | `0` on success |
