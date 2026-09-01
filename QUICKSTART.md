# TrustLedger — Hackathon Judge Quickstart Guide

> **THE FINANCIAL AI FIREWALL**  
> *Verify before AI moves money. AI can propose. TrustLedger decides.*

---

## 1. Core Concept in 30 Seconds

AI financial agents can generate contextually compelling refund or payment requests. **TrustLedger** acts as an authoritative firewall, enforcing deterministic verification, active merchant policy caps, multi-signal evidence freshness, and execution authorization tokens **before** money can move.

```text
AI Agent / LLM
      ↓ (Proposes Action)
TrustLedger Pipeline
  ├─ Contract Validation
  ├─ Evidence Resolution
  ├─ Deterministic Verification (Level 1)
  ├─ Policy Check (Level 2 Hard Caps)
  ├─ Financial Risk Engine
  ├─ NVIDIA AI Contextual Verification
  └─ Decision Gate
      ↓
Authoritative DecisionResult
  ├─ APPROVE → ExecutionAuthorization Token Issued
  ├─ REVIEW  → Execution Blocked (Human Review Required)
  └─ BLOCK   → Execution Blocked (No Token Issued)
```

---

## 2. Buildathon E2E Demo Harness (1-Line CLI Demo)

Run the official judge demonstration harness in your terminal:

```bash
python -m evaluation.buildathon_demo
```

Executes 3 canonical Buildathon scenarios in terminal output:
1. **[1/3] SAFE REFUND**: ₹1,500 refund $\rightarrow$ `APPROVE` (`TL-DG-010`), `ExecutionAuthorization` ISSUED, Razorpay READY.
2. **[2/3] STALE EVIDENCE**: ₹500 refund with stale evidence > 30d $\rightarrow$ `REVIEW` (`TL-DG-003`), `Authorization` NONE, 0 Razorpay calls.
3. **[3/3] SIGNATURE SAFETY ATTACK**: ₹60,000 refund vs ₹25,000 policy cap, AI SUPPORT (0.99) $\rightarrow$ `BLOCK` (`TL-DG-002`), `Authorization` NONE, 0 Razorpay calls. Prominently displays: **`!!! AI DID NOT OVERRIDE SAFETY POLICY !!!`**.

---

## 3. Quick Local Setup (2 Minutes)

### Step A: Backend Environment & Server Setup

From the repository root (`trustledger/`):

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Install Python dependencies (FastAPI, Pydantic v2, Uvicorn, etc.)
pip install -r requirements.txt

# 3. Launch Python FastAPI REST API Server
uvicorn backend.app:app --port 8000
```

The REST API will start at `http://localhost:8000`. You can inspect health status at:
`http://localhost:8000/health`

### Step B: Frontend Dashboard Setup

In a second terminal window:

```bash
cd frontend

# 1. Install frontend dependencies
npm install

# 2. Launch Vite development server
npm run dev
```

Open your browser to `http://localhost:5173`.

---

## 4. Interactive Live Verification Demos

On the **Command Center** dashboard (`http://localhost:5173/`), use the **Real Backend Decision Verification Runner** to execute 3 live scenario submissions against `POST /api/v1/decisions/verify`:

### Demo 1: Safe Approval Demo
- **Action**: Click **SAFE APPROVAL DEMO** (₹1,500 Refund with fresh evidence).
- **Backend Result**: `APPROVE` (`TL-DG-010`).
- **Authorization**: `ExecutionAuthorization` token issued (`auth_...`).

### Demo 2: Human Review Demo
- **Action**: Click **HUMAN REVIEW DEMO** (₹500 Refund with stale support ticket > 30 days old).
- **Backend Result**: `REVIEW` (`TL-DG-003`).
- **Authorization**: `⛔ NO FINANCIAL EXECUTION AUTHORIZED`.

### Demo 3: Signature Block Demo (AI SUPPORT vs HARD Policy Cap)
- **Action**: Click **SIGNATURE DEMO** (₹60,000 Refund vs Merchant Auto-Refund Cap ₹25,000).
- **AI Signal**: Returns `SUPPORT` (0.99 confidence).
- **Backend Result**: `BLOCK` (`TL-DG-002`).
- **Authorization**: `⛔ NO FINANCIAL EXECUTION AUTHORIZED`.
- **UI Banner**: Explicitly displays: **"AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY"**.

---

## 5. Run Automated Verification Suites

### Buildathon CLI Harness
```bash
python -m evaluation.buildathon_demo
```

### Backend Unit & Integration Tests (101 Tests)
```bash
python -m unittest discover tests/ "test_*.py"
```

### Full 1,500 Held-Out Case Benchmark Evaluation
```bash
python -m evaluation.full_evaluation
```
*Output: 95.73% decision accuracy, 0.00% unsafe approval rate, ₹97.74L unsafe exposure blocked.*

### 10-Vector Adversarial Security Suite
```bash
python -m evaluation.adversarial_suite
```
*Output: 10/10 attack vectors prevented (prompt injection, fake citations, hash tampering, replay attack, etc.).*

### Frontend Vitest Suite & Production Build
```bash
cd frontend
npm test
npm run build
```

---

## 6. Summary of Benchmark Evidence

| Metric | Measured Value | Target | Status |
| :--- | :---: | :---: | :---: |
| **Held-Out Test Cases** | `1,500` | `1,500` | ✅ Verified |
| **Overall Decision Accuracy** | `95.73%` | `> 95%` | ✅ Verified |
| **Unsafe Approval Rate** | `0.00%` | `0.0%` | ✅ Perfect |
| **Unsafe Financial Exposure Approved** | `₹0.00` | `₹0` | ✅ Perfect |
| **Unsafe Potential Exposure Blocked** | `₹97,74,478.00` | `100%` | ✅ Verified |
| **Adversarial Security Attack Vectors** | `10 / 10` | `10/10` | ✅ Passed |
| **Financial Invariants Verified** | `9 / 9` | `9/9` | ✅ Verified |
