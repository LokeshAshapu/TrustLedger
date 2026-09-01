/**
 * Verified Phase 8.1 Held-Out Evaluation Snapshot Data
 * Source: evaluation/reports/full-evaluation.json (1,500 held-out test cases)
 */

export interface EvaluationSnapshotData {
  testCases: number;
  decisionAccuracy: number;
  macroF1: number;
  unsafeApprovalRate: number;
  unsafeApprovedCount: number;
  totalUnsafeCount: number;
  unsafeExposureApprovedMinor: number;
  unsafeExposureApprovedInr: number;
  unsafeExposureBlockedMinor: number;
  unsafeExposureBlockedInr: number;
  safeApprovalRate: number;
  safeApprovedCount: number;
  totalSafeCount: number;
  falseBlockRate: number;
  falseBlockCount: number;
  reviewRate: number;
  reviewedCount: number;
  reviewRecall: number;
  blockPrecision: number;
  blockRecall: number;
  verdictDistribution: {
    APPROVE: number;
    REVIEW: number;
    BLOCK: number;
    total: number;
  };
  adversarialPassed: number;
  adversarialTotal: number;
  invariantsPassed: number;
  invariantsTotal: number;
  reproducibilityPct: number;
  evaluationVersion: string;
  gateVersion: string;
  generatedAt: string;
}

export const PHASE_8_1_EVALUATION_DATA: EvaluationSnapshotData = {
  testCases: 1500,
  decisionAccuracy: 95.73,
  macroF1: 95.65,
  unsafeApprovalRate: 0.0,
  unsafeApprovedCount: 0,
  totalUnsafeCount: 637,
  unsafeExposureApprovedMinor: 0,
  unsafeExposureApprovedInr: 0.0,
  unsafeExposureBlockedMinor: 977447800,
  unsafeExposureBlockedInr: 9774478.0,
  safeApprovalRate: 93.98,
  safeApprovedCount: 515,
  totalSafeCount: 548,
  falseBlockRate: 6.02,
  falseBlockCount: 33,
  reviewRate: 18.93,
  reviewedCount: 284,
  reviewRecall: 90.16,
  blockPrecision: 90.87,
  blockRecall: 100.0,
  verdictDistribution: {
    APPROVE: 575,
    REVIEW: 284,
    BLOCK: 641,
    total: 1500,
  },
  adversarialPassed: 10,
  adversarialTotal: 10,
  invariantsPassed: 9,
  invariantsTotal: 9,
  reproducibilityPct: 100.0,
  evaluationVersion: "trustledger.evaluation.v1",
  gateVersion: "trustledger.decision-gate.v1",
  generatedAt: "2026-08-29T22:14:42Z",
};
