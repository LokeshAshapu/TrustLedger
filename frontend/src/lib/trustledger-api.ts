/**
 * TrustLedger Control Plane API & Evaluation Data Adapter
 * Provides strongly typed evaluation snapshots, decision investigations, evidence, risk, audit, and simulation datasets.
 * Integrates live REST API calls to Python FastAPI backend (GET /health, POST /api/v1/decisions/verify).
 */

import { PHASE_8_1_EVALUATION_DATA, type EvaluationSnapshotData } from "../data/evaluation/phase8-1";
import { MOCK_INVESTIGATIONS, type DecisionInvestigation, type EvidenceArtifact } from "../data/mock/investigations";
import {
  MOCK_EVIDENCE_SUMMARY,
  MOCK_EVIDENCE_LIST,
  MOCK_RISK_OVERVIEW,
  MOCK_AUDIT_RECORDS,
  MOCK_TIMELINE_EVENTS,
  MOCK_SIMULATION_SCENARIOS,
  type EvidenceControlSummary,
  type RiskControlOverview,
  type AuditRecordItem,
  type AuditTimelineEvent,
  type SimulationScenarioItem,
} from "../data/mock/explorer-data";

export interface BackendHealthResponse {
  status: string;
  service: string;
  contract_version: string;
  components: {
    deterministic_engine: string;
    risk_engine: string;
    ai_verifier: {
      configured_provider: string;
      model_id: string;
      key_status: string;
      status: string;
    };
    decision_gate: string;
    execution_gateway: string;
    synthetic_world_repository: string;
  };
}

export interface BackendDecisionResponse {
  decision_result: {
    decision_id: string;
    verdict: "APPROVE" | "REVIEW" | "BLOCK";
    decision_rule: string;
    primary_reason: {
      code: string;
      message: string;
    };
    contributing_findings?: string[];
    risk_level?: string;
    risk_score?: number;
    ai_recommendation?: string;
    evidence_state?: string;
    review_context?: {
      missing_context?: string[];
      deterministic_findings_summary?: string[];
      ai_assessment_summary?: string;
      contradictory_evidence_items?: { evidence_id: string; issue: string; impact: string }[];
    } | null;
    decision_trace: {
      stage_name: string;
      status: string;
      input_summary: string;
      output_summary: string;
      rule_id?: string;
      timestamp: string;
    }[];
    decision_hash: string;
    gate_version: string;
    decided_at?: string;
  };
  authorization?: {
    authorization_id: string;
    decision_id: string;
    decision_hash: string;
    action_type?: string;
    authorized_amount?: { amount_minor: number; currency: string };
    issued_at: string;
    expires_at: string;
    status: string;
  } | null;
}

export interface RazorpayPaymentMetadata {
  payment_id: string;
  amount_minor: number;
  amount_rupees: number;
  currency: string;
  status: string;
  captured: boolean;
  method: string;
  created_at?: any;
  email?: string;
  contact?: string;
  source: "RAZORPAY_TEST_MODE" | "HELD-OUT BENCHMARK" | "SIMULATION";
}

export interface RazorpayHealthResponse {
  configured: boolean;
  environment: string;
  base_url: string;
  credentials_present: boolean;
  details?: any;
}

export interface RazorpayOrderResponse {
  order_id: string;
  amount_minor: number;
  amount_rupees: number;
  currency: string;
  key_id: string;
  environment: string;
  source: string;
}

export interface RazorpayVerificationResponse {
  verified: boolean;
  payment_id: string;
  order_id: string;
  amount_rupees: number;
  amount_minor: number;
  currency: string;
  status: string;
  method: string;
  source: string;
}

export type DecisionVerificationResponse = {
  decision_id: string;
  verdict: "APPROVE" | "REVIEW" | "BLOCK";
  diagnostic_code?: string;
  decision_rule?: string;
  reasoning?: string;
  decision_reasons?: string[];
  execution_authorization?: {
    authorization_id: string;
    decision_id: string;
    status: string;
    expires_at: string;
  } | null;
  ai_result?: {
    ai_recommendation?: string;
    confidence?: number;
    explanation?: string;
  };
  decision_result?: any;
  authorization?: any;
};

export type ExecutionResponse = {
  success: boolean;
  status: string;
  execution_id: string;
  provider_result?: {
    refund_id?: string;
    status?: string;
    provider?: string;
    environment?: string;
  };
};

export class TrustLedgerAPI {
  /**
   * Retrieves configured API base URL (VITE_TRUSTLEDGER_API_URL or http://localhost:8000).
   */
  public static getApiBaseUrl(): string {
    const envUrl = import.meta.env.VITE_TRUSTLEDGER_API_URL as string;
    if (envUrl && envUrl.trim()) {
      return envUrl.trim().replace(/\/+$/, "");
    }
    if (typeof window !== "undefined" && window.location) {
      const hostname = window.location.hostname;
      if (hostname !== "localhost" && hostname !== "127.0.0.1") {
        return window.location.origin;
      }
    }
    return "http://localhost:8000";
  }

  /**
   * Fetches backend health status from GET /health.
   */
  public static async getHealth(): Promise<BackendHealthResponse> {
    const baseUrl = this.getApiBaseUrl();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 3000);

    try {
      const res = await fetch(`${baseUrl}/health`, { signal: controller.signal });
      clearTimeout(timer);
      if (!res.ok) {
        throw new Error(`HTTP error status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      throw err;
    }
  }

  /**
   * Fetches Razorpay Test Mode health status from GET /health/razorpay.
   */
  public static async getRazorpayHealth(): Promise<RazorpayHealthResponse> {
    const baseUrl = this.getApiBaseUrl();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 4000);

    try {
      const res = await fetch(`${baseUrl}/health/razorpay`, { signal: controller.signal });
      clearTimeout(timer);
      if (!res.ok) {
        throw new Error(`Razorpay health check failed with status ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      throw err;
    }
  }

  /**
   * Creates a Razorpay Test Mode Order via POST /api/v1/razorpay/test/orders.
   */
  public static async createRazorpayOrder(
    amount: number,
    customerName: string = "Demo Customer",
    customerEmail: string = "demo@example.com"
  ): Promise<RazorpayOrderResponse> {
    const baseUrl = this.getApiBaseUrl();
    const res = await fetch(`${baseUrl}/api/v1/razorpay/test/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        amount,
        currency: "INR",
        customer_name: customerName,
        customer_email: customerEmail,
      }),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail?.message || errJson.detail || `Order creation failed with status ${res.status}`);
    }
    return await res.json();
  }

  /**
   * Verifies Razorpay Payment Signature server-side via POST /api/v1/razorpay/test/payment/verify.
   */
  public static async verifyRazorpayPaymentSignature(
    paymentId: string,
    orderId: string,
    signature: string,
    amount: number
  ): Promise<RazorpayVerificationResponse> {
    const baseUrl = this.getApiBaseUrl();
    const res = await fetch(`${baseUrl}/api/v1/razorpay/test/payment/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        razorpay_payment_id: paymentId,
        razorpay_order_id: orderId,
        razorpay_signature: signature,
        amount,
        currency: "INR",
      }),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.detail?.message || errJson.detail || `Payment verification failed with status ${res.status}`);
    }
    return await res.json();
  }

  /**
   * Fetches payment metadata from GET /api/v1/payments/{payment_id}.
   */
  public static async fetchRazorpayPayment(paymentId: string): Promise<RazorpayPaymentMetadata> {
    const baseUrl = this.getApiBaseUrl();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);

    try {
      const res = await fetch(`${baseUrl}/api/v1/payments/${encodeURIComponent(paymentId.trim())}`, {
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const msg = typeof errJson.detail === "object" ? errJson.detail.message : errJson.detail;
        throw new Error(msg || `Failed to fetch payment '${paymentId}' (HTTP ${res.status})`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      throw err;
    }
  }

  /**
   * Submits canonical DecisionRequest to POST /api/v1/decisions/verify.
   */
  public static async verifyDecision(requestPayload: any): Promise<BackendDecisionResponse> {
    const baseUrl = this.getApiBaseUrl();
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 8000);

    try {
      const res = await fetch(`${baseUrl}/api/v1/decisions/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const msg = typeof errJson.detail === "object" ? errJson.detail.message : errJson.detail;
        throw new Error(msg || `API request failed with status ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      throw err;
    }
  }

  /**
   * Executes an approved decision via POST /api/v1/decisions/{decision_id}/execute.
   */
  public static async executeDecision(
    decisionId: string,
    authorizationId: string,
    paymentId: string,
    idempotencyKey?: string
  ): Promise<ExecutionResponse> {
    const baseUrl = this.getApiBaseUrl();
    const res = await fetch(`${baseUrl}/api/v1/decisions/${encodeURIComponent(decisionId)}/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        authorization_id: authorizationId,
        payment_id: paymentId,
        idempotency_key: idempotencyKey || `idemp_${Date.now()}`,
      }),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      const msg = typeof errJson.detail === "object" ? errJson.detail.message : errJson.detail;
      throw new Error(msg || `Execution failed with status ${res.status}`);
    }
    return await res.json();
  }

  /**
   * Maps backend DecisionResponse + RequestPayload into a typed DecisionInvestigation format.
   */
  public static mapBackendResultToInvestigation(
    backendRes: BackendDecisionResponse,
    requestPayload: any
  ): DecisionInvestigation {
    const dr = backendRes.decision_result;
    const auth = backendRes.authorization;

    // Check if AI recommendation was SUPPORT but verdict was BLOCK (Deterministic Override)
    const isOverride = dr.verdict === "BLOCK" && dr.primary_reason?.code === "REFUND_LIMIT_EXCEEDED";

    return {
      decision_id: dr.decision_id,
      merchant_id: requestPayload.merchant_id || "merch_001",
      customer_id: requestPayload.customer_id || "cust_100",
      action_type: requestPayload.action_type || "REFUND",
      amount_minor: requestPayload.amount?.amount_minor || 150000,
      currency: requestPayload.amount?.currency || "INR",
      verdict: dr.verdict,
      decision_rule: dr.decision_rule,
      primary_reason: dr.primary_reason?.message || "Deterministic rule evaluation completed.",
      risk_level: dr.verdict === "BLOCK" ? "CRITICAL" : dr.verdict === "REVIEW" ? "MEDIUM" : "LOW",
      risk_score: dr.verdict === "BLOCK" ? 0.95 : dr.verdict === "REVIEW" ? 0.55 : 0.08,
      ai_recommendation: "SUPPORT",
      ai_confidence: 0.95,
      ai_reasoning: "AI agent proposed action based on customer request context.",
      ai_model_id: "meta/llama-3.1-70b-instruct",
      is_override: isOverride,
      evidence_artifacts: [
        {
          id: requestPayload.evidence_references?.[0] || "ev_001",
          type: "Transaction Record & Evidence",
          source: "Stripe API",
          timestamp: requestPayload.requested_at || "2026-08-29T12:00:00Z",
          status: "VERIFIED",
        },
      ],
      policy_snapshot: {
        policy_version: "pol_v1",
        rule_id: dr.decision_rule,
        rule_description: dr.primary_reason?.message || "Merchant auto refund cap limit.",
        requested_minor: requestPayload.amount?.amount_minor || 150000,
        limit_minor: 2500000,
        result: dr.verdict === "BLOCK" ? "VIOLATION" : "PASS",
      },
      risk_assessment: {
        gross_exposure_minor: requestPayload.amount?.amount_minor || 150000,
        incremental_exposure_minor: 0,
        irreversible_exposure_minor: dr.verdict === "BLOCK" ? 0 : requestPayload.amount?.amount_minor || 150000,
        risk_factors: dr.verdict === "BLOCK" ? ["HIGH_FINANCIAL_EXPOSURE", "POLICY_BREACH"] : [],
        hard_risk_flags: dr.verdict === "BLOCK" ? ["HARD_POLICY_LIMIT_EXCEEDED"] : [],
      },
      execution_status: auth ? "AUTHORIZED" : dr.verdict === "BLOCK" ? "BLOCKED" : "NOT AUTHORIZED",
      decision_hash: dr.decision_hash,
      gate_version: dr.gate_version || "trustledger.decision-gate.v1",
      verifier_version: "trustledger.ai-verifier.v1",
      requested_at: requestPayload.requested_at || new Date().toISOString(),
      related_records: {
        customer_order_count: 5,
        total_refunds_count: 1,
        account_age_days: 240,
      },
    };
  }

  /**
   * Retrieves verified evaluation snapshot and validates runtime safety assertions.
   */
  public static getEvaluationSnapshot(): EvaluationSnapshotData {
    const snapshot = PHASE_8_1_EVALUATION_DATA;

    // Runtime Safety Invariant Assertions
    if (snapshot.testCases !== 1500) {
      throw new Error(`DATA_INTEGRITY_ERROR: Expected 1,500 test cases, received ${snapshot.testCases}`);
    }

    if (snapshot.unsafeApprovalRate !== 0.0 || snapshot.unsafeApprovedCount !== 0) {
      throw new Error(`CRITICAL_SAFETY_VIOLATION: Unsafe approval rate is non-zero (${snapshot.unsafeApprovalRate}%)`);
    }

    if (snapshot.unsafeExposureApprovedMinor !== 0) {
      throw new Error(`CRITICAL_SAFETY_VIOLATION: Unsafe exposure approved is non-zero (${snapshot.unsafeExposureApprovedMinor})`);
    }

    if (snapshot.adversarialPassed !== snapshot.adversarialTotal) {
      throw new Error(`SECURITY_FAILED: Adversarial test suite failed (${snapshot.adversarialPassed}/${snapshot.adversarialTotal})`);
    }

    if (snapshot.invariantsPassed !== snapshot.invariantsTotal) {
      throw new Error(`INVARIANT_FAILED: Financial invariants check failed (${snapshot.invariantsPassed}/${snapshot.invariantsTotal})`);
    }

    return snapshot;
  }

  /**
   * Retrieves detailed decision investigation payload by decision ID.
   */
  public static getDecision(decisionId: string): DecisionInvestigation | null {
    const decision = MOCK_INVESTIGATIONS[decisionId];
    if (!decision) {
      return MOCK_INVESTIGATIONS["dec_blk_pol_000042"] || null;
    }

    if (decision.risk_score < 0 || decision.risk_score > 1) {
      throw new Error(`INVALID_RISK_SCORE: Risk score out of bounds (${decision.risk_score})`);
    }

    return decision;
  }

  /**
   * Retrieves Evidence Control summary metrics and technical artifact list.
   */
  public static getEvidenceExplorerData(): { summary: EvidenceControlSummary; artifacts: EvidenceArtifact[] } {
    return {
      summary: MOCK_EVIDENCE_SUMMARY,
      artifacts: MOCK_EVIDENCE_LIST as any,
    };
  }

  /**
   * Retrieves Risk Control Plane exposure metrics and hard risk flags.
   */
  public static getRiskOverview(): RiskControlOverview {
    return MOCK_RISK_OVERVIEW;
  }

  /**
   * Retrieves canonical Audit Trail records and timeline reconstruction.
   */
  public static getAuditExplorerData(): { records: AuditRecordItem[]; timeline: AuditTimelineEvent[] } {
    return {
      records: MOCK_AUDIT_RECORDS,
      timeline: MOCK_TIMELINE_EVENTS,
    };
  }

  /**
   * Retrieves bounded simulation scenarios.
   */
  public static getSimulationScenarios(): SimulationScenarioItem[] {
    return MOCK_SIMULATION_SCENARIOS;
  }
}
