import { describe, it, expect } from "vitest";
import { TrustLedgerAPI } from "../lib/trustledger-api";

describe("TrustLedger Phase 9D Control Plane Explorer & Bounded Simulator Data Adapter", () => {
  it("retrieves Evidence Explorer dataset with all 4 evidence status categories", () => {
    const { summary, artifacts } = TrustLedgerAPI.getEvidenceExplorerData();
    expect(summary.verified_count).toBe(1240);
    expect(summary.stale_count).toBe(145);
    expect(summary.conflicting_count).toBe(78);
    expect(summary.missing_count).toBe(37);

    const statuses = artifacts.map((a) => a.status);
    expect(statuses).toContain("VERIFIED");
    expect(statuses).toContain("STALE");
    expect(statuses).toContain("CONFLICTING");
    expect(statuses).toContain("MISSING");
  });

  it("verifies Risk Control Plane exposure metrics (0.00% unsafe approval, ₹97.74L blocked)", () => {
    const risk = TrustLedgerAPI.getRiskOverview();
    expect(risk.unsafe_exposure_approved_minor).toBe(0);
    expect(risk.unsafe_exposure_blocked_minor).toBe(977447800);
    expect(risk.hard_risk_flags.length).toBeGreaterThan(0);
  });

  it("verifies Audit Explorer records and microsecond timeline events", () => {
    const { records, timeline } = TrustLedgerAPI.getAuditExplorerData();
    expect(records.length).toBeGreaterThan(0);
    expect(timeline.length).toBeGreaterThan(0);
    expect(records[0].decision_hash).toBeDefined();
  });

  it("CRITICAL INVARIANT TEST: Verifies BLOCK and REVIEW decisions are strictly NOT AUTHORIZED for execution", () => {
    const scenarios = TrustLedgerAPI.getSimulationScenarios();
    const blockedScenarios = scenarios.filter((s) => s.verdict !== "APPROVE");

    blockedScenarios.forEach((scen) => {
      expect(scen.can_simulate).toBe(false);
      expect(["EXECUTION_BLOCKED", "NOT_AUTHORIZED"]).toContain(scen.authorization_state);
    });
  });

  it("verifies APPROVE decisions produce AUTHORIZED state eligible for simulation", () => {
    const scenarios = TrustLedgerAPI.getSimulationScenarios();
    const approvedScenarios = scenarios.filter((s) => s.verdict === "APPROVE");

    approvedScenarios.forEach((scen) => {
      expect(scen.can_simulate).toBe(true);
      expect(scen.authorization_state).toBe("AUTHORIZED");
    });
  });
});
