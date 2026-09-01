import { describe, it, expect } from "vitest";
import { TrustLedgerAPI } from "../lib/trustledger-api";

describe("TrustLedger Phase 9C Decision Investigation Data Adapter & Invariants", () => {
  it("retrieves representative decision investigation payloads", () => {
    const decision = TrustLedgerAPI.getDecision("dec_safe_000001");
    expect(decision).toBeDefined();
    expect(decision?.decision_id).toBe("dec_safe_000001");
    expect(decision?.verdict).toBe("APPROVE");
    expect(decision?.execution_status).toBe("AUTHORIZED");
  });

  it("verifies REVIEW required decision includes reviewer questions and stale evidence details", () => {
    const decision = TrustLedgerAPI.getDecision("dec_stale_006541");
    expect(decision).toBeDefined();
    expect(decision?.verdict).toBe("REVIEW");
    expect(decision?.execution_status).toBe("NOT AUTHORIZED");
    expect(decision?.review_context?.reviewer_questions.length).toBeGreaterThan(0);
    expect(decision?.evidence_artifacts[0].status).toBe("STALE");
  });

  it("CRITICAL INVARIANT TEST: Verifies AI SUPPORT + HARD policy violation = BLOCK (Deterministic Supremacy)", () => {
    const decision = TrustLedgerAPI.getDecision("dec_blk_pol_000042");
    expect(decision).toBeDefined();
    expect(decision?.ai_recommendation).toBe("SUPPORT");
    expect(decision?.policy_snapshot.result).toBe("VIOLATION");
    expect(decision?.verdict).toBe("BLOCK");
    expect(decision?.is_override).toBe(true);
    expect(decision?.execution_status).toBe("BLOCKED");
    expect(decision?.override_explanation).toContain("AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY");
  });

  it("verifies cryptographic audit hash metadata presence across all cases", () => {
    const ids = ["dec_safe_000001", "dec_stale_006541", "dec_blk_pol_000042"];
    ids.forEach((id) => {
      const dec = TrustLedgerAPI.getDecision(id);
      expect(dec?.decision_hash).toBeDefined();
      expect(dec?.decision_hash.length).toBeGreaterThan(20);
      expect(dec?.gate_version).toBe("trustledger.decision-gate.v1");
    });
  });
});
