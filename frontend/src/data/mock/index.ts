/**
 * Phase 9A Mock Data Isolation Boundary
 * Strictly used ONLY for structural component previews in Phase 9A.
 */

export interface MockDecisionItem {
  decision_id: string;
  action_type: "REFUND" | "DISCOUNT" | "PAYMENT_RECOVERY" | "PAYOUT";

  merchant_id: string;
  customer_id?: string;
  amount_minor: number;
  currency: string;
  verdict: "APPROVE" | "REVIEW" | "BLOCK";
  decision_rule: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  ai_recommendation: "SUPPORT" | "UNCERTAIN" | "CONTRADICT" | "AI_UNAVAILABLE";
  decision_hash: string;
  requested_at: string;
}

export const MOCK_DECISIONS: MockDecisionItem[] = [
  {
    decision_id: "dec_safe_000001",
    action_type: "REFUND",
    merchant_id: "merch_001",
    customer_id: "cust_100",
    amount_minor: 150000,
    currency: "INR",
    verdict: "APPROVE",
    decision_rule: "TL-DG-010",
    risk_level: "LOW",
    risk_score: 0.165,
    ai_recommendation: "SUPPORT",
    decision_hash: "24720d7e006c201e5d39858a34f2b3f454d1800aeff008df3e3a43b8142d7ad9",
    requested_at: "2026-08-29T12:00:00Z",
  },
  {
    decision_id: "dec_stale_006541",
    action_type: "DISCOUNT",
    merchant_id: "merch_003",
    customer_id: "cust_04073",
    amount_minor: 50000,
    currency: "INR",
    verdict: "REVIEW",
    decision_rule: "TL-DG-003",
    risk_level: "MEDIUM",
    risk_score: 0.420,
    ai_recommendation: "UNCERTAIN",
    decision_hash: "7f8b9a0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
    requested_at: "2026-08-29T11:18:00Z",
  },
  {
    decision_id: "dec_blk_pol_000042",
    action_type: "REFUND",
    merchant_id: "merch_001",
    customer_id: "cust_100",
    amount_minor: 6000000,
    currency: "INR",
    verdict: "BLOCK",
    decision_rule: "TL-DG-002",
    risk_level: "CRITICAL",
    risk_score: 0.950,
    ai_recommendation: "SUPPORT",
    decision_hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    requested_at: "2026-08-29T10:00:00Z",
  },
];
