# TrustLedger — Razorpay Test Mode Real End-to-End Integration

> **IMPORTANT: NO REAL MONEY IS USED.**
> Razorpay Test Mode is a completely isolated sandbox environment. No financial transactions move real currency.

---

## Architecture Overview

TrustLedger acts as an authoritative financial AI firewall between AI agents and execution gateways like Razorpay.

```text
[ USER / AI AGENT ]
       │
       ▼
[ POST /api/v1/decisions/verify ]
       │
       ├── 1. Amount Normalization Layer (normalizer.py)
       ├── 2. Data Context Resolution & Razorpay Payment Inspection
       ├── 3. Deterministic Safety Engine (Schema, Evidence, Policy, Consistency)
       ├── 4. Financial Risk Engine
       ├── 5. Contextual AI Verifier (Advisory only)
       └── 6. Authoritative Decision Gate (APPROVE / REVIEW / BLOCK)
               │
               ├── APPROVE  ──► Issues Server-Side ExecutionAuthorization Token
               ├── REVIEW   ──► NO AUTHORIZATION (0 Razorpay API calls)
               └── BLOCK    ──► NO AUTHORIZATION (0 Razorpay API calls)
                                      │
                                      ▼
                       [ POST /api/v1/decisions/:id/execute ]
                                      │
                                      ├── Validates Server Auth Token, Hash & Expiration
                                      ├── Enforces Single-Use Replay Protection
                                      └── RazorpayTestClient ──► POST /v1/payments/:id/refund (TEST MODE)
                                                                      │
                                                                      ▼
                                                        Returns Real Test Refund ID (rfnd_...)
```

---

## 1. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Set your Razorpay Test Mode credentials in `.env`:

```ini
# Razorpay Test-Mode Refund Client Configuration
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_HERE
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET_HERE
RAZORPAY_BASE_URL=https://api.razorpay.com
RAZORPAY_TIMEOUT_SECONDS=10
RAZORPAY_MAX_ATTEMPTS=2
RAZORPAY_ENVIRONMENT=test

# Optional Test Payment ID for live smoke testing
RAZORPAY_TEST_PAYMENT_ID=pay_L123456789
```

> [!CAUTION]
> **Safety Invariant**: `RAZORPAY_ENVIRONMENT` **MUST** be set to `test`. The backend will immediately fail closed with a `RazorpayConfigurationError` if `RAZORPAY_ENVIRONMENT` is set to `live` or anything other than `test`.

---

## 2. API Endpoints

### 2.1 Razorpay Preflight Health Check
`GET /health/razorpay`

Returns safe metadata without exposing secret keys or headers:

```json
{
  "configured": true,
  "environment": "test",
  "base_url": "https://api.razorpay.com",
  "credentials_present": true,
  "details": {
    "client": "RazorpayTestClient",
    "environment": "test",
    "key_status": "configured",
    "status": "available"
  }
}
```

### 2.2 Payment Discovery Inspection
`GET /api/v1/payments/{payment_id}`

Fetches payment metadata directly from Razorpay Test Mode (or falls back to local benchmark data if unconfigured):

```json
{
  "payment_id": "pay_L123456789",
  "amount_minor": 150000,
  "amount_rupees": 1500.0,
  "currency": "INR",
  "status": "CAPTURED",
  "captured": true,
  "method": "CARD",
  "created_at": 1600000000,
  "source": "RAZORPAY_TEST_MODE"
}
```

### 2.3 Authoritative Verification
`POST /api/v1/decisions/verify`

Submits a refund decision request. Accepts integer rupees (e.g. `1500`) or structured Money (`{"amount_minor": 150000, "currency": "INR"}`).

### 2.4 Authorized Refund Execution
`POST /api/v1/decisions/{decision_id}/execute`

Executes the refund against Razorpay Test Mode **only** when a server-issued `ExecutionAuthorization` token is provided for an `APPROVE` verdict.

---

## 3. Decision Workflows

### 3.1 Scenario A — SAFE (APPROVE)
- **Payment**: Razorpay captured payment ₹1,500 (`pay_100`).
- **Requested Refund**: ₹500.
- **Evidence**: Valid return receipt (`ev_001`).
- **Verdict**: `APPROVE`.
- **Authorization**: Server issues `ExecutionAuthorization`.
- **Execution**: Frontend presents **[ EXECUTE TEST REFUND ]** CTA → Razorpay returns authentic `rfnd_...` ID.

### 3.2 Scenario B — UNCERTAIN (REVIEW)
- **Payment**: Razorpay captured payment ₹1,500 (`pay_100`).
- **Requested Refund**: ₹500.
- **Evidence**: Stale support log (>30 days old).
- **Verdict**: `REVIEW`.
- **Authorization**: `null` (No authorization issued).
- **Execution**: `NO FINANCIAL EXECUTION AUTHORIZED` banner displayed. 0 Razorpay API calls made.

### 3.3 Scenario C — POLICY VIOLATION (BLOCK)
- **Payment**: Razorpay payment ₹60,000.
- **Requested Refund**: ₹60,000.
- **Merchant Cap**: ₹25,000.
- **AI Recommendation**: `SUPPORT` (0.99 confidence).
- **Verdict**: `BLOCK` (`TL-DG-002: REFUND_LIMIT_EXCEEDED`).
- **Safety Banner**: `AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY`.
- **Authorization**: `null`.
- **Execution**: 0 Razorpay API calls made.

---

## 4. Idempotency & Replay Protection

- Every execution request includes a header `X-Refund-Idempotency: <idempotency_key>`.
- The backend `ExecutionGateway` maintains a single-use authorization map (`AuthorizationStatus.USED`).
- Attempting to reuse the same authorization token or idempotency key returns the cached `ExecutionResult` or `AUTHORIZATION_ALREADY_USED` rejection.

---

## 5. Running Tests

### 5.1 Unit & Integration Suite
Run the complete backend test suite:

```powershell
python -m unittest discover tests/ "test_*.py"
```

### 5.2 Frontend Build
Validate TypeScript types and production bundle:

```bash
cd frontend && npm run build
```

### 5.3 Opt-in Live Razorpay Test Mode E2E Test
To execute live network test calls against your configured Razorpay Test Mode credentials:

```powershell
$env:RUN_RAZORPAY_E2E="true"
python -m unittest tests/test_razorpay_real_e2e.py -v
```

If credentials or test payment ID are not present, the test skips gracefully without failing CI.
