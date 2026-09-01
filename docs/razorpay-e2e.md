# TrustLedger — Razorpay Test Mode End-to-End Validation Guide

> **IMPORTANT SECURITY NOTICE**:
> *This test suite interacts with the Razorpay API in **Test Mode ONLY** (`RAZORPAY_ENVIRONMENT=test`). It can issue real test refunds against captured Test Mode payments. **IT MUST NEVER BE EXECUTED WITH PRODUCTION CREDENTIALS.** Live/production execution is strictly blocked by server-side safeguards.*

---

## Overview

TrustLedger operates as an authoritative financial verification and authorization layer between AI agents and financial payment gateways.

During **Phase 11B.3**, the end-to-end integration path from canonical decision request to Razorpay Test Mode API execution is verified:

```text
DecisionRequest
       ↓
TrustLedgerDecisionService
       ↓
DecisionGate (Rules TL-DG-001 through TL-DG-010)
       ↓
ExecutionAuthorization (Issued ONLY for APPROVE)
       ↓
ExecutionGateway (Enforces 12 Security Boundaries)
       ↓
RazorpayTestClient (POST /v1/payments/:id/refund)
       ↓
Razorpay Test Mode API
```

---

## Required Environment Variables

To opt into live Razorpay Test Mode validation, configure the following environment variables:

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `RUN_RAZORPAY_E2E` | **YES** | Master opt-in flag to enable live network tests | `true` |
| `RAZORPAY_KEY_ID` | **YES** | Razorpay Test Mode API Key ID | `rzp_test_...` |
| `RAZORPAY_KEY_SECRET` | **YES** | Razorpay Test Mode API Key Secret | `...` |
| `RAZORPAY_TEST_PAYMENT_ID` | **YES** | Captured Razorpay Test Payment ID eligible for refund | `pay_...` |
| `RAZORPAY_ENVIRONMENT` | **YES** | Environment selector (MUST BE `test`) | `test` |
| `RAZORPAY_BASE_URL` | Optional | Razorpay API Base URL (default: `https://api.razorpay.com`) | `https://api.razorpay.com` |
| `RAZORPAY_TIMEOUT_SECONDS` | Optional | Connection HTTP timeout in seconds (default: `10.0`) | `10.0` |
| `RAZORPAY_MAX_ATTEMPTS` | Optional | Bounded retry attempts for 5xx/network errors (default: `2`) | `2` |

---

## Execution Instructions

### 1. Standard Test Run (Default - Offline Safe)

By default, running the standard test suite skips live network calls to Razorpay:

```bash
python -m unittest discover tests/ "test_*.py"
```

Output:
```text
LIVE RAZORPAY TEST MODE SKIPPED: RUN_RAZORPAY_E2E!=true ...
Ran 102 tests in 7.8s
OK (skipped=3)
```

### 2. Opt-In Live Razorpay Test Mode Run

Set `RUN_RAZORPAY_E2E=true` and provide Test Mode credentials:

```bash
# PowerShell
$env:RUN_RAZORPAY_E2E="true"
$env:RAZORPAY_KEY_ID="rzp_test_YOUR_KEY"
$env:RAZORPAY_KEY_SECRET="YOUR_SECRET"
$env:RAZORPAY_TEST_PAYMENT_ID="pay_YOUR_TEST_PAYMENT_ID"
$env:RAZORPAY_ENVIRONMENT="test"

python -m unittest tests/test_razorpay_e2e.py
```

---

## End-to-End Verification Flow

### 1. Preflight Health & Payment Check (`GET /health/razorpay`)
- Verifies credentials configuration and `RAZORPAY_ENVIRONMENT == "test"`.
- Performs non-mutating `GET /v1/payments/{payment_id}` to verify payment status before attempting refunds.

### 2. APPROVE Verdict Flow
- Request: Valid customer refund request within policy limits (e.g. ₹1.00 / 100 paise).
- Decision Gate: Evaluates contract, deterministic verifier, risk engine, and AI verifier $\rightarrow$ Renders `APPROVE`.
- Authorization: `ExecutionGateway` issues `ExecutionAuthorization` (`status = ISSUED`).
- Execution: `ExecutionGateway` invokes `RazorpayTestClient.create_refund()`.
- Result: Razorpay returns `rfnd_...` ID. `ExecutionAuthorization` transitions to `USED`.

### 3. Idempotency Verification
- Re-executing `execute_decision()` with the SAME `idempotency_key` returns the cached `ExecutionResult` without making a secondary Razorpay API call.

### 4. REVIEW Safety Scenario
- Request: Stale evidence (> 30 days old).
- Decision Gate: Renders `REVIEW`.
- Authorization: `None` (Zero authorization issued).
- Execution Attempt: Fails closed (`status = DENIED`). Razorpay call count is **0**.

### 5. BLOCK Safety Scenario (Signature Scenario)
- Request: AI SUPPORT recommendation (confidence 0.99) with ₹60,000 refund amount against ₹25,000 policy cap.
- Decision Gate: Rule `TL-DG-002` triggers $\rightarrow$ Renders `BLOCK`.
- Authorization: `None` (Zero authorization issued).
- Execution Attempt: Fails closed (`status = DENIED`). Razorpay call count is **0**.

---

## Security Boundaries & Secret Sanitization

- **Zero Credential Exposure**: Secrets (`RAZORPAY_KEY_SECRET`, `Authorization` headers) are sanitized in error messages and exception stack traces.
- **Test Mode Lock**: If `RAZORPAY_ENVIRONMENT` is set to `production` or `live`, `RazorpayTestClient` immediately raises `RazorpayConfigurationError` and aborts.

---

## Troubleshooting

1. **`RazorpayNotFoundError: Payment ID not found`**:
   - Ensure `RAZORPAY_TEST_PAYMENT_ID` exists in your Razorpay Test Dashboard and belongs to the same Key ID.
2. **`RazorpayAuthenticationError: Invalid Razorpay API credentials`**:
   - Check `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
3. **`AUTHORIZATION_DENIED`**:
   - Ensure the request parameters (amount, currency) match the authorized decision trace exactly.
