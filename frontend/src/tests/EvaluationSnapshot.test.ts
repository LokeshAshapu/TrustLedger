import { describe, it, expect } from "vitest";
import { TrustLedgerAPI } from "../lib/trustledger-api";

describe("TrustLedger Phase 8.1 Evaluation Snapshot Data Adapter", () => {
  it("retrieves verified snapshot without throwing integrity errors", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    expect(snapshot).toBeDefined();
    expect(snapshot.testCases).toBe(1500);
  });

  it("verifies zero unsafe approvals requirement (0.00%)", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    expect(snapshot.unsafeApprovalRate).toBe(0.0);
    expect(snapshot.unsafeApprovedCount).toBe(0);
    expect(snapshot.unsafeExposureApprovedMinor).toBe(0);
    expect(snapshot.unsafeExposureApprovedInr).toBe(0.0);
  });

  it("verifies decision accuracy and macro F1 metrics", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    expect(snapshot.decisionAccuracy).toBe(95.73);
    expect(snapshot.macroF1).toBe(95.65);
    expect(snapshot.safeApprovalRate).toBe(93.98);
    expect(snapshot.falseBlockRate).toBe(6.02);
  });

  it("verifies verdict distribution sum matches total test cases (1,500)", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    const { APPROVE, REVIEW, BLOCK, total } = snapshot.verdictDistribution;
    expect(APPROVE).toBe(575);
    expect(REVIEW).toBe(284);
    expect(BLOCK).toBe(641);
    expect(APPROVE + REVIEW + BLOCK).toBe(total);
    expect(total).toBe(1500);
  });

  it("verifies 10/10 adversarial vectors passed and 9/9 financial invariants verified", () => {
    const snapshot = TrustLedgerAPI.getEvaluationSnapshot();
    expect(snapshot.adversarialPassed).toBe(10);
    expect(snapshot.adversarialTotal).toBe(10);
    expect(snapshot.invariantsPassed).toBe(9);
    expect(snapshot.invariantsTotal).toBe(9);
    expect(snapshot.reproducibilityPct).toBe(100.0);
  });
});
