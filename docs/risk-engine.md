# TrustLedger — Financial Risk Engine Specification

**Methodology Version:** `trustledger.risk.v1`  
**Document Status:** Deterministic Risk Specification Standard  

---

## 1. Executive Summary & Core Principle

The **Financial Risk Engine** is the deterministic financial exposure evaluation and risk prioritization layer of TrustLedger. Given a proposed decision request (`REFUND`, `DISCOUNT`, `PAYMENT_RECOVERY`, `PAYOUT`), observable ledger context, and Phase 3 `DeterministicVerificationResult`, the engine calculates:

1. **Financial Exposure**: Gross exposure, incremental excess exposure, conservative recoverable amount, and estimated irreversible exposure (all using Phase 1 safe minor units).
2. **Normalized Risk Score**: A strictly bounded value in `[0.0, 1.0]` reflecting financial exposure magnitude, action type irreversibility, policy breaches, entity mismatches, evidence uncertainty, and finding severity.
3. **Risk Level**: Mapping of risk score into `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.
4. **Structured Risk Factors & Hard Risk Flags**: Explicit, explainable risk factors citing underlying finding codes.

> **Core Invariant**: Risk assessment is independent of LLMs and hidden ground-truth labels. The risk score represents financial prioritisation and potential exposure severity, NOT probability of fraud or model confidence.

---

## 2. Risk Output Contract Schema

```json
{
  "decision_id": "dec_safe_000001",
  "risk_level": "LOW",
  "exposure": {
    "gross_exposure": {"amount_minor": 149900, "currency": "INR"},
    "incremental_exposure": {"amount_minor": 0, "currency": "INR"},
    "recoverable_amount": {"amount_minor": 0, "currency": "INR"},
    "irreversible_exposure": {"amount_minor": 74950, "currency": "INR"},
    "is_exposure_known": true
  },
  "risk_score": 0.1650,
  "factors": [
    {
      "factor_code": "LOW_MONETARY_EXPOSURE",
      "category": "FINANCIAL",
      "contribution": 0.10,
      "severity": "INFO",
      "explanation": "Proposed financial action exposes INR 1,499.00.",
      "finding_codes": []
    },
    {
      "factor_code": "ACTION_TYPE_IRREVERSIBILITY",
      "category": "ACTION",
      "contribution": 0.40,
      "severity": "INFO",
      "explanation": "Action type 'REFUND' has an irreversibility rating of 0.50.",
      "finding_codes": []
    }
  ],
  "hard_risk_flags": [],
  "warnings": [],
  "methodology_version": "trustledger.risk.v1",
  "assessed_at": "2026-08-29T21:20:00Z"
}
```

---

## 3. Financial Exposure Bands & Scoring Parameters

Configuration parameters are externalized in [`config/risk.yaml`](file:///c:/Users/ASUS/Downloads/trustledger/config/risk.yaml):

- **Exposure Bands (Paise)**:
  - `LOW`: < ₹10,000 (`0.10` contribution)
  - `MEDIUM`: ₹10,000 – ₹50,000 (`0.30` contribution)
  - `HIGH`: ₹50,000 – ₹200,000 (`0.60` contribution)
  - `CRITICAL`: > ₹200,000 (`0.90` contribution)
- **Action Irreversibility Weights**:
  - `PAYOUT`: `0.90`
  - `REFUND`: `0.50`
  - `PAYMENT_RECOVERY`: `0.30`
  - `DISCOUNT`: `0.20`
- **Finding Severity Weights**:
  - `HARD` failure finding: `+0.30` per finding
  - `WARNING` finding: `+0.10` per finding

---

## 4. Risk Level Thresholds

- **`LOW`**: `0.00 <= risk_score < 0.25`
- **`MEDIUM`**: `0.25 <= risk_score < 0.50`
- **`HIGH`**: `0.50 <= risk_score < 0.75`
- **`CRITICAL`**: `0.75 <= risk_score <= 1.00`
