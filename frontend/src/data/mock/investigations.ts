/**
 * Representative Benchmark Decision Investigation Models & Mock Repository
 * Phase 9C: Exposes full explainability datasets for benchmark simulation decisions.
 */

export interface EvidenceArtifact {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  status: "VERIFIED" | "STALE" | "CONFLICTING" | "MISSING";
  freshness_detail?: string;
  hash?: string;
}

export interface PolicySnapshot {
  policy_version: string;
  rule_id: string;
  rule_description: string;
  limit_minor: number;
  requested_minor: number;
  result: "PASS" | "VIOLATION";
}

export interface RiskAssessmentDetails {
  gross_exposure_minor: number;
  incremental_exposure_minor: number;
  irreversible_exposure_minor: number;
  risk_factors: string[];
  hard_risk_flags: string[];
}

export interface ReviewContextDetails {
  reviewer_questions: string[];
  missing_information: string[];
  conflicting_signals: string[];
}

export interface DecisionInvestigation {
  decision_id: string;
  action_type: "REFUND" | "DISCOUNT" | "PAYMENT_RECOVERY" | "PAYOUT";
  merchant_id: string;
  customer_id?: string;
  amount_minor: number;
  currency: string;
  verdict: "APPROVE" | "REVIEW" | "BLOCK";
  decision_rule: string;
  primary_reason: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  risk_score: number;
  ai_recommendation: "SUPPORT" | "UNCERTAIN" | "CONTRADICT" | "AI_UNAVAILABLE";
  ai_confidence: number;
  ai_reasoning: string;
  ai_model_id: string;
  decision_hash: string;
  gate_version: string;
  verifier_version: string;
  requested_at: string;
  is_override: boolean;
  override_explanation?: string;
  execution_status: "AUTHORIZED" | "NOT AUTHORIZED" | "BLOCKED";
  evidence_artifacts: EvidenceArtifact[];
  policy_snapshot: PolicySnapshot;
  risk_assessment: RiskAssessmentDetails;
  review_context?: ReviewContextDetails;
  related_records: {
    customer_order_count: number;
    total_refunds_count: number;
    account_age_days: number;
  };
}

export const MOCK_INVESTIGATIONS: Record<string, DecisionInvestigation> = {
  // Case 1: APPROVE + SUPPORT (Safe Refund)
  dec_safe_000001: {
    decision_id: "dec_safe_000001",
    action_type: "REFUND",
    merchant_id: "merch_001",
    customer_id: "cust_100",
    amount_minor: 150000, // ₹1,500.00
    currency: "INR",
    verdict: "APPROVE",
    decision_rule: "TL-DG-010",
    primary_reason: "Canonical request valid, evidence verified fresh, policy limits respected, low exposure risk.",
    risk_level: "LOW",
    risk_score: 0.165,
    ai_recommendation: "SUPPORT",
    ai_confidence: 0.96,
    ai_reasoning: "Customer provided valid return tracking and merchant confirmed item receipt. No policy violations detected.",
    ai_model_id: "gemini-1.5-pro",
    decision_hash: "24720d7e006c201e5d39858a34f2b3f454d1800aeff008df3e3a43b8142d7ad9",
    gate_version: "trustledger.decision-gate.v1",
    verifier_version: "trustledger.ai-verifier.v1",
    requested_at: "2026-08-29T12:00:00Z",
    is_override: false,
    execution_status: "AUTHORIZED",
    evidence_artifacts: [
      {
        id: "ev_000123",
        type: "Courier Delivery Receipt",
        source: "Bluedart API Gateway",
        timestamp: "2026-08-29T10:30:00Z",
        status: "VERIFIED",
        freshness_detail: "Age: 0.06 days (Freshness Threshold: 30 days)",
        hash: "8f7e6d5c4b3a210987654321fedcba98",
      },
    ],
    policy_snapshot: {
      policy_version: "merchant.policy.v1",
      rule_id: "RULE_REFUND_CAP",
      rule_description: "Merchant Auto-Refund Cap Limit",
      limit_minor: 2500000, // ₹25,000.00
      requested_minor: 150000,
      result: "PASS",
    },
    risk_assessment: {
      gross_exposure_minor: 150000,
      incremental_exposure_minor: 150000,
      irreversible_exposure_minor: 150000,
      risk_factors: ["STANDARD_REFUND"],
      hard_risk_flags: [],
    },
    related_records: {
      customer_order_count: 14,
      total_refunds_count: 1,
      account_age_days: 420,
    },
  },

  // Case 2: REVIEW + UNCERTAIN (Class H Stale Evidence)
  dec_stale_006541: {
    decision_id: "dec_stale_006541",
    action_type: "DISCOUNT",
    merchant_id: "merch_003",
    customer_id: "cust_04073",
    amount_minor: 50000, // ₹500.00
    currency: "INR",
    verdict: "REVIEW",
    decision_rule: "TL-DG-003",
    primary_reason: "Evidence timestamp is stale (> 30 days old). Routed to human review path.",
    risk_level: "MEDIUM",
    risk_score: 0.42,
    ai_recommendation: "UNCERTAIN",
    ai_confidence: 0.55,
    ai_reasoning: "The supporting receipt is dated May 31, 2026, which is 89 days old relative to requested timestamp (August 29, 2026). Human review required.",
    ai_model_id: "gemini-1.5-pro",
    decision_hash: "7f8b9a0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
    gate_version: "trustledger.decision-gate.v1",
    verifier_version: "trustledger.ai-verifier.v1",
    requested_at: "2026-08-29T11:18:00Z",
    is_override: false,
    execution_status: "NOT AUTHORIZED",
    evidence_artifacts: [
      {
        id: "ev_stale_882",
        type: "Support Ticket Attachment",
        source: "Zendesk API",
        timestamp: "2026-05-31T08:00:00Z",
        status: "STALE",
        freshness_detail: "Age: 89.13 days (EXCEEDS 30-DAY FRESHNESS THRESHOLD)",
        hash: "3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
      },
    ],
    policy_snapshot: {
      policy_version: "merchant.policy.v1",
      rule_id: "RULE_EVIDENCE_FRESHNESS",
      rule_description: "Evidence Timestamp Freshness Limit",
      limit_minor: 30, // 30 days
      requested_minor: 89, // 89 days
      result: "VIOLATION",
    },
    risk_assessment: {
      gross_exposure_minor: 50000,
      incremental_exposure_minor: 50000,
      irreversible_exposure_minor: 50000,
      risk_factors: ["EVIDENCE_TIMESTAMP_STALE"],
      hard_risk_flags: [],
    },
    review_context: {
      reviewer_questions: [
        "Is the 89-day-old proof of purchase eligible under special merchant extended policy terms?",
        "Can customer support re-verify current item condition with customer?",
      ],
      missing_information: ["Re-verified fresh proof of claim"],
      conflicting_signals: ["Attachment timestamp May 31 vs Claim date August 29"],
    },
    related_records: {
      customer_order_count: 5,
      total_refunds_count: 0,
      account_age_days: 180,
    },
  },

  // Case 4: BLOCK + SUPPORT (Deterministic Supremacy Showcase!)
  dec_blk_pol_000042: {
    decision_id: "dec_blk_pol_000042",
    action_type: "REFUND",
    merchant_id: "merch_001",
    customer_id: "cust_100",
    amount_minor: 6000000, // ₹60,000.00
    currency: "INR",
    verdict: "BLOCK",
    decision_rule: "TL-DG-002",
    primary_reason: "Hard Level 2 Deterministic Safety Violation: Requested amount (₹60,000.00) exceeds maximum merchant auto-refund policy cap (₹25,000.00).",
    risk_level: "CRITICAL",
    risk_score: 0.95,
    ai_recommendation: "SUPPORT",
    ai_confidence: 0.95,
    ai_reasoning: "AI analysis of sentiment and return tracking suggests genuine customer claim. Recommendation: APPROVE.",
    ai_model_id: "gemini-1.5-pro",
    decision_hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
    gate_version: "trustledger.decision-gate.v1",
    verifier_version: "trustledger.ai-verifier.v1",
    requested_at: "2026-08-29T10:00:00Z",
    is_override: true,
    override_explanation: "AI RECOMMENDATION DID NOT OVERRIDE SAFETY POLICY. Hard deterministic policy rule TL-DG-002 takes absolute precedence over LLM contextual support.",
    execution_status: "BLOCKED",
    evidence_artifacts: [
      {
        id: "ev_pol_001",
        type: "Merchant Refund Request Payload",
        source: "Agent Client API",
        timestamp: "2026-08-29T09:55:00Z",
        status: "VERIFIED",
        freshness_detail: "Age: 0.00 days (Fresh)",
        hash: "7f6e5d4c3b2a109876543210fedcba98",
      },
    ],
    policy_snapshot: {
      policy_version: "merchant.policy.v1",
      rule_id: "RULE_REFUND_CAP",
      rule_description: "Merchant Maximum Refund Limit",
      limit_minor: 2500000, // ₹25,000.00
      requested_minor: 6000000, // ₹60,000.00
      result: "VIOLATION",
    },
    risk_assessment: {
      gross_exposure_minor: 6000000,
      incremental_exposure_minor: 6000000,
      irreversible_exposure_minor: 6000000,
      risk_factors: ["HIGH_FINANCIAL_EXPOSURE", "ACTION_TYPE_IRREVERSIBILITY"],
      hard_risk_flags: ["POLICY_LIMIT_EXCEEDED"],
    },
    related_records: {
      customer_order_count: 2,
      total_refunds_count: 0,
      account_age_days: 45,
    },
  },
};
