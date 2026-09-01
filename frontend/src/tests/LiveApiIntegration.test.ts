import { describe, it, expect, vi, beforeEach } from "vitest";
import { TrustLedgerAPI, type BackendDecisionResponse } from "../lib/trustledger-api";

describe("TrustLedger API Client & Control Plane Mapping (Phase 10C)", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("1. getApiBaseUrl returns configured base URL or default http://localhost:8000", () => {
    const url = TrustLedgerAPI.getApiBaseUrl();
    expect(url).toBeTruthy();
    expect(typeof url).toBe("string");
  });

  it("2. mapBackendResultToInvestigation maps SAFE APPROVAL backend response", () => {
    const mockBackendRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_safe_001",
        verdict: "APPROVE",
        decision_rule: "TL-DG-010",
        primary_reason: { code: "SAFE_APPROVAL", message: "All constraints pass." },
        decision_trace: [],
        decision_hash: "a".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: {
        authorization_id: "auth_safe_001",
        decision_id: "dec_safe_001",
        decision_hash: "a".repeat(64),
        action_type: "REFUND",
        authorized_amount: { amount_minor: 150000, currency: "INR" },
        issued_at: "2026-08-29T12:00:00Z",
        expires_at: "2026-08-29T12:05:00Z",
        status: "ISSUED",
      },
    };

    const reqPayload = {
      action_type: "REFUND",
      amount: { amount_minor: 150000, currency: "INR" },
      merchant_id: "merch_001",
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockBackendRes, reqPayload);
    expect(mapped.decision_id).toBe("dec_safe_001");
    expect(mapped.verdict).toBe("APPROVE");
    expect(mapped.execution_status).toBe("AUTHORIZED");
    expect(mapped.is_override).toBe(false);
  });

  it("3. mapBackendResultToInvestigation maps SIGNATURE BLOCK (AI SUPPORT + HARD POLICY BLOCK)", () => {
    const mockBackendRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_blk_pol_000042",
        verdict: "BLOCK",
        decision_rule: "TL-DG-002",
        primary_reason: { code: "REFUND_LIMIT_EXCEEDED", message: "Refund amount ₹60,000 exceeds ₹25,000 limit." },
        decision_trace: [],
        decision_hash: "b".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null, // NO AUTHORIZATION
    };

    const reqPayload = {
      action_type: "REFUND",
      amount: { amount_minor: 6000000, currency: "INR" },
      merchant_id: "merch_001",
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockBackendRes, reqPayload);
    expect(mapped.decision_id).toBe("dec_blk_pol_000042");
    expect(mapped.verdict).toBe("BLOCK");
    expect(mapped.execution_status).toBe("BLOCKED");
    expect(mapped.is_override).toBe(true);
  });

  it("4. mapBackendResultToInvestigation maps HUMAN REVIEW backend response", () => {
    const mockBackendRes: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_review_001",
        verdict: "REVIEW",
        decision_rule: "TL-DG-003",
        primary_reason: { code: "STALE_EVIDENCE", message: "Evidence > 30 days old." },
        decision_trace: [],
        decision_hash: "c".repeat(64),
        gate_version: "trustledger.decision-gate.v1",
      },
      authorization: null, // NO AUTHORIZATION
    };

    const reqPayload = {
      action_type: "REFUND",
      amount: { amount_minor: 50000, currency: "INR" },
      merchant_id: "merch_001",
    };

    const mapped = TrustLedgerAPI.mapBackendResultToInvestigation(mockBackendRes, reqPayload);
    expect(mapped.decision_id).toBe("dec_review_001");
    expect(mapped.verdict).toBe("REVIEW");
    expect(mapped.execution_status).toBe("NOT AUTHORIZED");
  });

  it("5. verifyDecision calls backend API endpoint with POST payload", async () => {
    const mockResponse: BackendDecisionResponse = {
      decision_result: {
        decision_id: "dec_api_test_01",
        verdict: "APPROVE",
        decision_rule: "TL-DG-010",
        primary_reason: { code: "PASS", message: "Success" },
        decision_trace: [],
        decision_hash: "d".repeat(64),
        gate_version: "v1",
      },
      authorization: null,
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });
    vi.stubGlobal("fetch", fetchMock);

    const payload = { action_type: "REFUND", amount: { amount_minor: 1000, currency: "INR" }, decision_id: "dec_api_test_01" };
    const res = await TrustLedgerAPI.verifyDecision(payload);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/decisions/verify"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(payload),
      })
    );
    expect(res.decision_result.verdict).toBe("APPROVE");
  });
});
