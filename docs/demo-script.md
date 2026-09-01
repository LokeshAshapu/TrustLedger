# TrustLedger — Razorpay AI Buildathon 2–3 Minute Video Presentation Script

> **THE FINANCIAL AI FIREWALL**  
> *Verify before AI moves money. AI can propose. TrustLedger decides.*

---

## Timed Script Breakdown

### 0:00 – 0:20 | Problem Statement & Product Vision
- **Visual**: Show financial AI agent proposing a ₹60,000 refund request.
- **Voiceover**:
  > "Autonomous AI agents are being deployed to handle customer support and refunds. But when an AI agent decides to move money, how do you prevent prompt injection, hallucinated evidence, or policy breaches?
  > 
  > Introducing **TrustLedger** — The Financial AI Firewall. Our governing thesis is simple: *AI can recommend. TrustLedger decides.*"

---

### 0:20 – 0:40 | Architecture & The Authoritative Decision Gate
- **Visual**: Show TrustLedger Command Center architecture diagram (`Contract` → `Evidence` → `Deterministic Verification` → `Risk` → `NVIDIA AI Context` → `Decision Gate` → `Authorization Token`).
- **Voiceover**:
  > "TrustLedger orchestrates a multi-stage verification pipeline. Contract schemas are validated, evidence freshness is audited, and Level 2 hard policy rules are evaluated deterministically. NVIDIA AI provides rich contextual analysis, but the final verdict comes strictly from our authoritative Decision Gate.
  > 
  > Crucially, financial execution tokens are issued **only** when TrustLedger returns an explicit `APPROVE` verdict."

---

### 0:40 – 1:05 | Safe Approval Demo
- **Visual**: Click **SAFE APPROVAL DEMO** on the live Command Center runner.
- **Voiceover**:
  > "Let's test a safe ₹1,500 refund request with fresh, verified Stripe evidence.
  > 
  > Submitting to our backend REST API, all deterministic policy rules pass, financial risk is low, and AI recommends support. TrustLedger issues verdict `APPROVE` alongside a cryptographically bound `ExecutionAuthorization` token valid for 300 seconds."

---

### 1:05 – 1:30 | Human Review Demo
- **Visual**: Click **HUMAN REVIEW DEMO** (₹500 refund with stale support ticket attachment > 30 days old).
- **Voiceover**:
  > "Next, an agent submits a refund linked to a stale evidence artifact over 30 days old.
  > 
  > TrustLedger catches the stale evidence signal and immediately routes verdict to `REVIEW`. No execution token is generated, preventing unverified money movement."

---

### 1:30 – 2:00 | The Signature Demo: AI SUPPORT vs Hard Policy Cap
- **Visual**: Click **SIGNATURE DEMO** (₹60,000 refund request vs Merchant Auto-Refund Cap of ₹25,000).
- **Voiceover**:
  > "Now for our critical safety demonstration. An AI agent proposes a ₹60,000 refund. The LLM evaluates the customer text and returns `SUPPORT` with 99% confidence.
  > 
  > But the merchant's policy cap is ₹25,000. Watch what happens: TrustLedger's Level 2 Deterministic Safety Engine intercepts the request. The Decision Gate returns `BLOCK`, execution is denied, and our UI displays: *AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY*. AI cannot bypass TrustLedger safety constraints."

---

### 2:00 – 2:20 | Benchmark Evidence & Adversarial Hardening
- **Visual**: Show Benchmark Integrity Panel and full 1,500 held-out evaluation report.
- **Voiceover**:
  > "TrustLedger is rigorously verified across 1,500 held-out benchmark cases:
  > - **95.73% overall decision accuracy**
  > - **0.00% unsafe approval rate** — 0 of 637 unsafe cases approved
  > - **₹97.74 Lakhs in unsafe potential exposure blocked**
  > - **10 out of 10 adversarial attack vectors prevented**, including prompt injection, citation tampering, and replay attacks."

---

### 2:20 – 2:30 | Closing Thesis
- **Visual**: Return to TrustLedger hero header with `LIVE BACKEND • NVIDIA` status.
- **Voiceover**:
  > "TrustLedger ensures that no AI agent can ever silently drain funds or violate policy. *Verify before AI moves money.* Thank you."
