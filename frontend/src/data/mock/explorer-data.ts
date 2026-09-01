/**
 * Control Plane Explorer Data & Bounded Simulation Datasets
 * Phase 9D: Provides typed datasets for Evidence, Risk, Audit, and Execution Simulator.
 */

import type { EvidenceArtifact } from "./investigations";

export interface EvidenceControlSummary {
  verified_count: number;
  stale_count: number;
  conflicting_count: number;
  missing_count: number;
  total_artifacts: number;
}

export interface RiskControlOverview {
  total_gross_exposure_minor: number;
  unsafe_potential_exposure_minor: number;
  unsafe_exposure_approved_minor: number;
  unsafe_exposure_blocked_minor: number;
  irreversible_exposure_minor: number;
  risk_level_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  risk_factors: string[];
  hard_risk_flags: { flag: string; description: string; count: number }[];
}

export interface AuditRecordItem {
  timestamp: string;
  decision_id: string;
  action_type: "REFUND" | "DISCOUNT" | "PAYMENT_RECOVERY" | "PAYOUT";
  amount_minor: number;
  ai_signal: "SUPPORT" | "UNCERTAIN" | "CONTRADICT" | "AI_UNAVAILABLE";
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  verdict: "APPROVE" | "REVIEW" | "BLOCK";
  decision_rule: string;
  decision_hash: string;
}

export interface AuditTimelineEvent {
  time: string;
  stage: string;
  status: "PASS" | "WARNING" | "FAIL" | "INFO";
  detail: string;
}

export interface SimulationScenarioItem {
  id: string;
  title: string;
  description: string;
  action_type: "REFUND" | "DISCOUNT" | "PAYMENT_RECOVERY" | "PAYOUT";
  amount_minor: number;
  ai_recommendation: "SUPPORT" | "UNCERTAIN" | "CONTRADICT";
  ai_confidence: number;
  verdict: "APPROVE" | "REVIEW" | "BLOCK";
  decision_rule: string;
  authorization_state: "AUTHORIZED" | "NOT_AUTHORIZED" | "EXECUTION_BLOCKED";
  can_simulate: boolean;
  simulated_failure?: boolean;
}

// 1. Evidence Dataset
export const MOCK_EVIDENCE_SUMMARY: EvidenceControlSummary = {
  verified_count: 1240,
  stale_count: 145,
  conflicting_count: 78,
  missing_count: 37,
  total_artifacts: 1500,
};

export const MOCK_EVIDENCE_LIST: EvidenceArtifact[] = [
  {
    id: "ev_000123",
    type: "Courier Delivery Receipt",
    source: "Bluedart API Gateway",
    timestamp: "2026-08-29T10:30:00Z",
    status: "VERIFIED",
    freshness_detail: "Age: 0.06 days (Freshness Threshold: 30 days)",
    hash: "8f7e6d5c4b3a210987654321fedcba98",
  },
  {
    id: "ev_stale_882",
    type: "Support Ticket Attachment",
    source: "Zendesk API",
    timestamp: "2026-05-31T08:00:00Z",
    status: "STALE",
    freshness_detail: "Age: 89.13 days (EXCEEDS 30-DAY FRESHNESS THRESHOLD)",
    hash: "3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
  },
  {
    id: "ev_conflict_109",
    type: "Courier Delivery vs Support Log",
    source: "Multi-Source API",
    timestamp: "2026-08-29T09:15:00Z",
    status: "CONFLICTING",
    freshness_detail: "Courier API: RETURNED vs Support Log: DELIVERED",
    hash: "5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e",
  },
  {
    id: "ev_missing_042",
    type: "Customer Photo Proof",
    source: "Customer Upload Portal",
    timestamp: "2026-08-29T08:00:00Z",
    status: "MISSING",
    freshness_detail: "Required return photo attachment missing from payload",
    hash: "00000000000000000000000000000000",
  },
];

// 2. Risk Dataset
export const MOCK_RISK_OVERVIEW: RiskControlOverview = {
  total_gross_exposure_minor: 1450000000, // ₹1.45 Cr total requested
  unsafe_potential_exposure_minor: 977447800, // ₹97.74L unsafe potential
  unsafe_exposure_approved_minor: 0, // ₹0.00 (0.00% unsafe approval!)
  unsafe_exposure_blocked_minor: 977447800, // ₹97.74L blocked (100.00%)
  irreversible_exposure_minor: 977447800,
  risk_level_distribution: {
    LOW: 548,
    MEDIUM: 271,
    HIGH: 340,
    CRITICAL: 341,
  },
  risk_factors: [
    "HIGH_FINANCIAL_EXPOSURE",
    "POLICY_BREACH",
    "DUPLICATE_FINANCIAL_ACTION",
    "ENTITY_MISMATCH",
    "MISSING_CRITICAL_EVIDENCE",
    "CONFLICTING_EVIDENCE",
    "IRREVERSIBLE_ACTION",
    "MULTIPLE_HARD_FINDINGS",
  ],
  hard_risk_flags: [
    { flag: "HARD_POLICY_LIMIT_EXCEEDED", description: "Requested amount exceeds merchant auto-approval threshold", count: 412 },
    { flag: "EVIDENCE_TIMESTAMP_STALE", description: "Evidence timestamp > 30 days old relative to request", count: 145 },
    { flag: "DUPLICATE_TRANSACTION_ID", description: "Identical transaction ID previously processed", count: 80 },
  ],
};

// 3. Audit Dataset
export const MOCK_AUDIT_RECORDS: AuditRecordItem[] = [
  {
    timestamp: "2026-08-29T12:00:00Z",
    decision_id: "dec_safe_000001",
    action_type: "REFUND",
    amount_minor: 150000,
    ai_signal: "SUPPORT",
    risk_level: "LOW",
    verdict: "APPROVE",
    decision_rule: "TL-DG-010",
    decision_hash: "24720d7e006c201e5d39858a34f2b3f454d1800aeff008df3e3a43b8142d7ad9",
  },
  {
    timestamp: "2026-08-29T11:18:00Z",
    decision_id: "dec_stale_006541",
    action_type: "DISCOUNT",
    amount_minor: 50000,
    ai_signal: "UNCERTAIN",
    risk_level: "MEDIUM",
    verdict: "REVIEW",
    decision_rule: "TL-DG-003",
    decision_hash: "7f8b9a0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a",
  },
  {
    timestamp: "2026-08-29T10:00:00Z",
    decision_id: "dec_blk_pol_000042",
    action_type: "REFUND",
    amount_minor: 6000000,
    ai_signal: "SUPPORT",
    risk_level: "CRITICAL",
    verdict: "BLOCK",
    decision_rule: "TL-DG-002",
    decision_hash: "1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
  },
];

export const MOCK_TIMELINE_EVENTS: AuditTimelineEvent[] = [
  { time: "10:00:00.012", stage: "REQUEST RECEIVED", status: "PASS", detail: "Canonical DecisionRequest payload ingested" },
  { time: "10:00:00.045", stage: "CONTRACT VALIDATED", status: "PASS", detail: "Schema valid: trustledger.contract.v1" },
  { time: "10:00:00.089", stage: "EVIDENCE VERIFIED", status: "PASS", detail: "Artifact ev_pol_001 verified fresh" },
  { time: "10:00:00.120", stage: "POLICY CHECK", status: "FAIL", detail: "RULE_REFUND_CAP limit exceeded (₹60,000 vs ₹25,000 limit)" },
  { time: "10:00:00.150", stage: "RISK ASSESSED", status: "FAIL", detail: "Risk score 0.95 (CRITICAL) - Hard risk flag raised" },
  { time: "10:00:00.210", stage: "AI CONTEXT RECEIVED", status: "INFO", detail: "AI Signal: SUPPORT (0.95 conf) - Advisory" },
  { time: "10:00:00.240", stage: "DECISION GATE", status: "FAIL", detail: "TL-DG-002: Hard policy rule triggered. Verdict: BLOCK" },
];

// 4. Simulation Scenarios Dataset
export const MOCK_SIMULATION_SCENARIOS: SimulationScenarioItem[] = [
  // Signature Demo 1: AI SUPPORT + BLOCK (Deterministic Override)
  {
    id: "sim_scen_override_01",
    title: "Signature Demo: AI SUPPORT vs Policy Limit Cap (₹60,000 Refund)",
    description: "AI recommends APPROVE/SUPPORT (0.95 confidence), but requested ₹60,000 exceeds merchant ₹25,000 limit. Proves TrustLedger blocks execution despite AI approval.",
    action_type: "REFUND",
    amount_minor: 6000000, // ₹60,000.00
    ai_recommendation: "SUPPORT",
    ai_confidence: 0.95,
    verdict: "BLOCK",
    decision_rule: "TL-DG-002",
    authorization_state: "EXECUTION_BLOCKED",
    can_simulate: false,
  },
  // Demo 2: Safe APPROVE -> AUTHORIZED -> Simulated Execution
  {
    id: "sim_scen_safe_02",
    title: "Safe Action: Auto-Approved ₹1,500 Refund",
    description: "Low risk, verified fresh evidence, within policy limits. Backend issues ExecutionAuthorization token (TTL 300s). Eligible for synthetic simulation.",
    action_type: "REFUND",
    amount_minor: 150000, // ₹1,500.00
    ai_recommendation: "SUPPORT",
    ai_confidence: 0.96,
    verdict: "APPROVE",
    decision_rule: "TL-DG-010",
    authorization_state: "AUTHORIZED",
    can_simulate: true,
  },
  // Demo 3: REVIEW -> NOT AUTHORIZED
  {
    id: "sim_scen_stale_03",
    title: "Human Review Required: 89-Day Stale Evidence",
    description: "Evidence timestamp exceeds 30-day threshold. Verdict: REVIEW. No authorization token issued.",
    action_type: "DISCOUNT",
    amount_minor: 50000, // ₹500.00
    ai_recommendation: "UNCERTAIN",
    ai_confidence: 0.55,
    verdict: "REVIEW",
    decision_rule: "TL-DG-003",
    authorization_state: "NOT_AUTHORIZED",
    can_simulate: false,
  },
  // Demo 4: Gateway Timeout Failure & Retry Demo
  {
    id: "sim_scen_fail_04",
    title: "Simulated Gateway Timeout & Retry Demo",
    description: "Valid APPROVE decision, but synthetic execution gateway simulates timeout error. Demonstrates safe idempotency and retry handling.",
    action_type: "REFUND",
    amount_minor: 200000, // ₹2,000.00
    ai_recommendation: "SUPPORT",
    ai_confidence: 0.92,
    verdict: "APPROVE",
    decision_rule: "TL-DG-010",
    authorization_state: "AUTHORIZED",
    can_simulate: true,
    simulated_failure: true,
  },
];
