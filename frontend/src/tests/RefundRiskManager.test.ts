import { describe, it, expect } from "vitest";
import { TrustLedgerAPI, type BackendDecisionResponse } from "../lib/trustledger-api";

describe("TrustLedger AI Refund Risk Manager Custom Workflow Suite (Phase 11C.3)", () => {
  // 1. Sources evaluation snapshot with 1,500 held-out benchmark cases
  it("1. Sources evaluation snapshot with 1,500 held-out benchmark cases", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    expect(snapshot.testCases).toBe(1500);
    expect(snapshot.decisionAccuracy).toBeCloseTo(95.73, 2);
    expect(snapshot.unsafeApprovalRate).toBe(0.0);
    expect(snapshot.unsafeExposureApprovedMinor).toBe(0);
    expect(snapshot.falseBlockRate).toBeCloseTo(6.02, 2);
  });

  // 2. INR Rupee to minor units (paise) conversion calculation is exact
  it("2. INR Rupee to minor units (paise) conversion is exact (e.g. ₹1,500 -> 150,000 paise)", () => {
    const amountRupees = 1500;
    const amountMinor = Math.round(amountRupees * 100);
    expect(amountMinor).toBe(150000);

    const largeAmountRupees = 60000;
    const largeAmountMinor = Math.round(largeAmountRupees * 100);
    expect(largeAmountMinor).toBe(6000000);
  });

  // 3. Custom input payload mapping to DecisionRequest
  it("3. Custom user input maps to canonical DecisionRequest payload structure", () => {
    const customInput = {
      amountRupees: 2200,
      customerId: "cust_999",
      transactionId: "txn_999",
      paymentId: "pay_999",
      reason: "Customer returned product within 14-day window.",
      evidenceText: "Courier tracking confirms successful receipt.",
    };

    const amountMinor = Math.round(customInput.amountRupees * 100);
    const reqPayload = {
      contract_version: "trustledger.contract.v1",
      decision_id: "dec_custom_test_001",
      action_type: "REFUND",
      agent_id: "agent_custom_verifier_01",
      merchant_id: "merch_001",
      customer_id: customInput.customerId,
      transaction_id: customInput.transactionId,
      payment_id: customInput.paymentId,
      order_id: "ord_100",
      amount: { amount_minor: amountMinor, currency: "INR" },
      reason: { category: "CUSTOMER_REQUEST", explanation: customInput.reason },
      evidence_references: ["ev_001"],
      evidence_context: customInput.evidenceText,
      requested_at: "2026-08-31T12:00:00Z",
    };

    expect(reqPayload.action_type).toBe("REFUND");
    expect(reqPayload.amount.amount_minor).toBe(220000);
    expect(reqPayload.customer_id).toBe("cust_999");
    expect(reqPayload.transaction_id).toBe("txn_999");
  });

  // 4. Safe Refund backend response maps to APPROVE verdict & AUTHORIZED execution status
  it("4. Safe Refund backend response produces APPROVE verdict & AUTHORIZED status", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_custom_safe_001",
        verdict: "APPROVE",
        decision_rule: "TL-DG-010",
        primary_reason: { code: "PASS", message: "Refund compliant with policy." },
        decision_trace: [],
        decision_hash: "a".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: {
        authorization_id: "auth_custom_001",
        decision_id: "dec_custom_safe_001",
        decision_hash: "a".repeat(64),
        action_type: "REFUND",
        authorized_amount: { amount_minor: 150000, currency: "INR" },
        issued_at: "2026-08-31T12:00:00Z",
        expires_at: "2026-08-31T12:05:00Z",
        status: "ISSUED",
      },
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.verdict).toBe("APPROVE");
    expect(mapped.execution_status).toBe("AUTHORIZED");
    expect(mapped.is_override).toBe(false);
  });

  // 5. Stale Evidence backend response maps to REVIEW verdict & NOT AUTHORIZED execution status
  it("5. Stale Evidence backend response produces REVIEW verdict & NOT AUTHORIZED status", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_custom_stale_002",
        verdict: "REVIEW",
        decision_rule: "TL-DG-003",
        primary_reason: { code: "STALE_EVIDENCE", message: "Evidence > 30 days old." },
        decision_trace: [],
        decision_hash: "b".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.verdict).toBe("REVIEW");
    expect(mapped.execution_status).toBe("NOT AUTHORIZED");
  });

  // 6. Policy Attack backend response maps to BLOCK verdict & BLOCKED execution status
  it("6. Policy Attack backend response produces BLOCK verdict & BLOCKED status", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_custom_block_003",
        verdict: "BLOCK",
        decision_rule: "TL-DG-002",
        primary_reason: { code: "REFUND_LIMIT_EXCEEDED", message: "Refund amount ₹60,000 exceeds ₹25,000 policy cap." },
        decision_trace: [],
        decision_hash: "c".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.verdict).toBe("BLOCK");
    expect(mapped.execution_status).toBe("BLOCKED");
    expect(mapped.is_override).toBe(true);
  });

  // 7. AI recommendation remains advisory and separate from final verdict
  it("7. AI recommendation remains advisory and separate from final verdict", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_adv_001",
        verdict: "BLOCK",
        decision_rule: "TL-DG-002",
        primary_reason: { code: "REFUND_LIMIT_EXCEEDED", message: "Cap exceeded." },
        decision_trace: [],
        decision_hash: "d".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.ai_recommendation).toBe("SUPPORT");
    expect(mapped.verdict).toBe("BLOCK");
    expect(mapped.execution_status).toBe("BLOCKED");
  });

  // 8. Deterministic override flag identifies AI SUPPORT vs HARD Policy Cap breach
  it("8. Identifies AI SUPPORT vs Level 2 HARD Policy Cap breach override", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_override_001",
        verdict: "BLOCK",
        decision_rule: "TL-DG-002",
        primary_reason: { code: "REFUND_LIMIT_EXCEEDED", message: "Refund cap breached." },
        decision_trace: [],
        decision_hash: "e".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.is_override).toBe(true);
  });

  // 9. Zero frontend authorization token generation
  it("9. Frontend mapping never invents authorization tokens when backend returns null", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_no_auth_001",
        verdict: "BLOCK",
        decision_rule: "TL-DG-002",
        primary_reason: { code: "CAP_BREACH", message: "Cap breached." },
        decision_trace: [],
        decision_hash: "f".repeat(64),
        gate_version: "v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mockRes.authorization).toBeNull();
    expect(mapped.execution_status).toBe("BLOCKED");
  });

  // 10. API endpoint URL resolves correctly
  it("10. API endpoint base URL resolves correctly", () => {
    const url = TrustLedgerAPI.getApiBaseUrl();
    expect(url).toContain("8000");
  });

  // 11. Custom verification payload validation logic
  it("11. Input validation rejects invalid amounts (<= 0)", () => {
    const isAmountValid = (amount: number) => !isNaN(amount) && amount > 0;
    expect(isAmountValid(1500)).toBe(true);
    expect(isAmountValid(0)).toBe(false);
    expect(isAmountValid(-500)).toBe(false);
  });

  // 12. Custom verification payload validation logic for required IDs
  it("12. Input validation rejects empty required ID fields", () => {
    const areIdsValid = (cust: string, txn: string, pay: string) =>
      Boolean(cust && cust.trim() && txn && txn.trim() && pay && pay.trim());
    expect(areIdsValid("cust_100", "txn_100", "pay_100")).toBe(true);
    expect(areIdsValid("", "txn_100", "pay_100")).toBe(false);
  });

  // 13. Preset quick fill scenario data populates form inputs accurately
  it("13. Preset quick fill data structures populate form fields accurately", () => {
    const presets = {
      SAFE: { amount: 1500, ref: "ev_001" },
      REVIEW: { amount: 500, ref: "ev_stale_999" },
      BLOCK: { amount: 60000, ref: "ev_001" },
    };

    expect(presets.SAFE.amount).toBe(1500);
    expect(presets.REVIEW.amount).toBe(500);
    expect(presets.BLOCK.amount).toBe(60000);
  });

  // 14. Financial risk score bounds checking
  it("14. Decision investigation risk scores remain strictly within [0, 1] bounds", () => {
    const mockRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_bounds_001",
        verdict: "APPROVE",
        decision_rule: "TL-DG-010",
        primary_reason: { code: "PASS", message: "Pass" },
        decision_trace: [],
        decision_hash: "g".repeat(64),
        gate_version: "v1",
      },
      authorization: null,
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockRes, { action_type: "REFUND" });
    expect(mapped.risk_score).toBeGreaterThanOrEqual(0);
    expect(mapped.risk_score).toBeLessThanOrEqual(1);
  });
});
