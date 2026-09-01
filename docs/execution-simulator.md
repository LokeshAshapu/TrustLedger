# TrustLedger — Bounded Financial Execution Simulator Specification

**Simulator Version:** `trustledger.execution-simulator.v1`  
**Document Status:** Bounded Financial Execution Standard  

---

## 1. Executive Summary & Non-Bypass Architecture

The **Bounded Financial Execution Simulator** provides a deterministic synthetic sandbox execution layer demonstrating how TrustLedger safely controls AI agent financial proposals (`REFUND`, `DISCOUNT`, `PAYMENT_RECOVERY`, `PAYOUT`) without moving real money or connecting to external payment gateways.

TrustLedger enforces the following strict non-bypass execution boundary:

```
AI Agent -> TrustLedger -> Decision Gate (APPROVE) -> ExecutionAuthorization -> ExecutionGateway -> Synthetic Ledger
```

> **Core Invariants**:
> 1. **Zero Real Money**: All operations execute on a synthetic local ledger. No Razorpay or external banking APIs are invoked.
> 2. **Non-Bypass Architecture**: The AI agent has zero direct access to the financial simulator. Direct calls without a valid `ExecutionAuthorization` fail immediately.
> 3. **Verdict Boundary**: `REVIEW` and `BLOCK` decisions CANNOT issue authorizations or execute financial actions.

---

## 2. Authorization Lifecycle & Security Controls

```
[DecisionResult: APPROVE] ──> authorize() ──> [ISSUED Authorization]
                                                    │
                                                    ├── submit to execute() ──> [USED Authorization] ──> [SUCCESS Result]
                                                    ├── time > TTL ──────────> [EXPIRED Authorization] ──> [REJECTED Result]
                                                    └── re-submit ───────────> [AUTHORIZATION_ALREADY_USED] ──> [REJECTED Result]
```

- **Cryptographic Hash Binding**: Every token is bound to `decision_hash` (SHA-256). The gateway recomputes the canonical hash before execution and rejects if altered (`DECISION_HASH_MISMATCH`).
- **Single-Use Replay Protection**: Tokens transition to `USED` state upon successful execution. Re-submitting returns `AUTHORIZATION_ALREADY_USED`.
- **Tamper Protection**: Modifying `action_type`, `amount`, or `currency` returns `ACTION_MISMATCH`, `AMOUNT_MISMATCH`, or `CURRENCY_MISMATCH`.
- **Short TTL Expiration**: Authorizations expire after a configurable duration (default: 300 seconds).

---

## 3. Execution Result Schema

```json
{
  "execution_id": "exec_8f3a12b4",
  "authorization_id": "auth_9c2d15e8",
  "decision_id": "dec_safe_000001",
  "status": "SUCCESS",
  "action_type": "REFUND",
  "amount": {"amount_minor": 149900, "currency": "INR"},
  "external_reference": "ref_sync_00001001",
  "failure_code": "NONE",
  "executed_at": "2026-08-29T21:55:00Z",
  "idempotency_key": "idemp_auth_9c2d15e8"
}
```
