/**
 * TrustLedger — Canonical Financial Decision Contracts
 * Contract Version: trustledger.contract.v1
 */

export const CURRENT_CONTRACT_VERSION = 'trustledger.contract.v1';

/**
 * Supported Financial Action Types
 */
export enum ActionType {
  REFUND = 'REFUND',
  DISCOUNT = 'DISCOUNT',
  PAYMENT_RECOVERY = 'PAYMENT_RECOVERY',
  PAYOUT = 'PAYOUT',
}

/**
 * Decision Gate Verdict Outcomes
 */
export enum VerdictType {
  APPROVE = 'APPROVE',
  REVIEW = 'REVIEW',
  BLOCK = 'BLOCK',
}

/**
 * Decision Lifecycle States
 */
export enum LifecycleState {
  RECEIVED = 'RECEIVED',
  NORMALIZED = 'NORMALIZED',
  EVIDENCE_CHECK = 'EVIDENCE_CHECK',
  POLICY_CHECK = 'POLICY_CHECK',
  CONSISTENCY_CHECK = 'CONSISTENCY_CHECK',
  RISK_ASSESSMENT = 'RISK_ASSESSMENT',
  AI_VERIFICATION = 'AI_VERIFICATION',
  VERDICT = 'VERDICT',
  READY_FOR_EXECUTION = 'READY_FOR_EXECUTION',
  HUMAN_REVIEW = 'HUMAN_REVIEW',
  BLOCKED = 'BLOCKED',
  EXECUTING = 'EXECUTING',
  EXECUTED = 'EXECUTED',
  FAILED = 'FAILED',
}

/**
 * Controlled Reason Categories
 */
export enum ReasonCategory {
  DUPLICATE_PAYMENT = 'DUPLICATE_PAYMENT',
  CUSTOMER_REQUEST = 'CUSTOMER_REQUEST',
  NON_DELIVERY = 'NON_DELIVERY',
  SERVICE_FAILURE = 'SERVICE_FAILURE',
  PROMOTIONAL_DISCOUNT = 'PROMOTIONAL_DISCOUNT',
  PAYMENT_FAILURE = 'PAYMENT_FAILURE',
  SETTLEMENT = 'SETTLEMENT',
  OTHER = 'OTHER',
}

/**
 * Controlled Evidence Types
 */
export enum EvidenceType {
  TRANSACTION = 'TRANSACTION',
  ORDER = 'ORDER',
  PAYMENT_ATTEMPT = 'PAYMENT_ATTEMPT',
  REFUND_HISTORY = 'REFUND_HISTORY',
  CUSTOMER_HISTORY = 'CUSTOMER_HISTORY',
  POLICY = 'POLICY',
  INVOICE = 'INVOICE',
  PAYOUT = 'PAYOUT',
  DELIVERY = 'DELIVERY',
  OTHER = 'OTHER',
}

/**
 * Evidence Verification Statuses
 */
export enum EvidenceVerificationStatus {
  UNVERIFIED = 'UNVERIFIED',
  VERIFIED = 'VERIFIED',
  FAILED = 'FAILED',
  CONFLICTING = 'CONFLICTING',
  MISSING = 'MISSING',
}

/**
 * Financial Risk Levels
 */
export enum RiskLevel {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

/**
 * Execution Statuses
 */
export enum ExecutionStatus {
  NOT_STARTED = 'NOT_STARTED',
  QUEUED = 'QUEUED',
  EXECUTING = 'EXECUTING',
  SUCCEEDED = 'SUCCEEDED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

/**
 * System and Operational Actor Types
 */
export enum ActorType {
  AI_AGENT = 'AI_AGENT',
  TRUSTLEDGER = 'TRUSTLEDGER',
  HUMAN = 'HUMAN',
  FINANCIAL_SYSTEM = 'FINANCIAL_SYSTEM',
}

/**
 * Validation Error Codes
 */
export enum ValidationErrorCategory {
  INVALID_ACTION_TYPE = 'INVALID_ACTION_TYPE',
  INVALID_AMOUNT = 'INVALID_AMOUNT',
  INVALID_CURRENCY = 'INVALID_CURRENCY',
  MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD',
  INVALID_TIMESTAMP = 'INVALID_TIMESTAMP',
  INVALID_VERDICT = 'INVALID_VERDICT',
  INVALID_CONFIDENCE = 'INVALID_CONFIDENCE',
  INVALID_EVIDENCE_REFERENCE = 'INVALID_EVIDENCE_REFERENCE',
  DUPLICATE_EVIDENCE_REFERENCE = 'DUPLICATE_EVIDENCE_REFERENCE',
  INVALID_POLICY_VERSION = 'INVALID_POLICY_VERSION',
  INVALID_DISCOUNT_SPEC = 'INVALID_DISCOUNT_SPEC',
  INVALID_RISK_LEVEL = 'INVALID_RISK_LEVEL',
  INVALID_EVIDENCE_STATUS = 'INVALID_EVIDENCE_STATUS',
  INVALID_EXECUTION_STATUS = 'INVALID_EXECUTION_STATUS',
  INVALID_ACTOR_TYPE = 'INVALID_ACTOR_TYPE',
  MALFORMED_CONTRACT_VERSION = 'MALFORMED_CONTRACT_VERSION',
}

/**
 * Reusable Safe Monetary Representation
 * Represents money safely using integer minor units (e.g. Paise for INR: ₹1,499 -> 149900).
 */
export interface Money {
  amount_minor: number; // Non-negative integer minor unit (paise, cents, etc.)
  currency: string;     // ISO 4217 uppercase currency code (e.g., INR, USD)
}

/**
 * Reason Specification
 */
export interface ReasonSpec {
  category: ReasonCategory;
  explanation?: string;
}

/**
 * Discount Specification for FIXED_AMOUNT or PERCENTAGE representation
 */
export type DiscountSpec =
  | {
      type: 'FIXED_AMOUNT';
      value: Money;
    }
  | {
      type: 'PERCENTAGE';
      percentage_points: number; // e.g. 15.0 for 15% discount
    };

/**
 * Canonical Decision Request Contract
 */
export interface DecisionRequest {
  contract_version: string;
  decision_id: string;
  action_type: ActionType;
  agent_id: string;
  merchant_id: string;
  customer_id?: string | null;
  transaction_id?: string | null;
  order_id?: string | null;
  amount: Money;
  discount_spec?: DiscountSpec | null;
  reason: ReasonSpec;
  evidence_references: string[];
  requested_at: string;
  metadata?: Record<string, unknown> | null;
}

/**
 * Evidence Artifact Contract with Provenance Data
 */
export interface Evidence {
  contract_version: string;
  evidence_id: string;
  evidence_type: EvidenceType;
  source: string;              // System of origin (e.g., Shopify, Zendesk, Stripe)
  source_record_id: string;    // Record ID in origin system
  timestamp: string;           // Provenance creation timestamp (ISO 8601)
  content_hash?: string | null; // Cryptographic SHA-256 content hash if available
  verification_status: EvidenceVerificationStatus;
  metadata?: Record<string, unknown> | null;
}

/**
 * Versioned Policy Snapshot Contract
 */
export interface PolicySnapshot {
  contract_version: string;
  policy_id: string;
  merchant_id: string;
  action_type: ActionType;
  rules: Array<{
    rule_id: string;
    rule_name: string;
    description?: string;
    threshold_value?: number | string | boolean | null;
    is_hard_constraint: boolean;
  }>;
  effective_from: string;
  effective_until?: string | null;
  policy_version: string;
}

/**
 * Verification Result Contract
 * Distinguishes deterministic check results from AI verification outputs.
 */
export interface VerificationResult {
  contract_version: string;
  decision_id: string;
  verdict: VerdictType;
  confidence: number; // Normalized 0.0 - 1.0 confidence signal (not absolute truth)
  risk_level: RiskLevel;
  evidence_result: {
    evidence_score: number; // 0.0 - 1.0 score
    verified_count: number;
    missing_references: string[];
  };
  policy_result: {
    passed: boolean;
    violations: Array<{
      policy_id: string;
      rule_id: string;
      message: string;
    }>;
  };
  consistency_result: {
    is_consistent: boolean;
    contradictions: string[];
  };
  ai_result: {
    verdict_recommendation: VerdictType;
    reasoning_summary: string;
    detected_risk_factors: string[];
    confidence: number;
  };
  reasons: string[];
  missing_evidence: string[];
  verification_started_at: string;
  verification_completed_at: string;
  verifier_version: string;
}

/**
 * Execution Result Contract
 */
export interface ExecutionResult {
  contract_version: string;
  execution_id: string;
  decision_id: string;
  status: ExecutionStatus;
  provider: string;
  provider_reference?: string | null;
  amount: Money;
  executed_at: string;
  error_code?: string | null;
  error_message?: string | null;
  idempotency_key: string;
}

/**
 * Append-Only Audit Record Contract
 */
export interface AuditRecord {
  contract_version: string;
  event_id: string;
  decision_id: string;
  event_type: string;
  actor_type: ActorType;
  actor_id: string;
  timestamp: string;
  previous_state?: LifecycleState | null;
  new_state: LifecycleState;
  reason: string;
  metadata?: Record<string, unknown> | null;
  correlation_id: string;
}

/**
 * Standardized Validation Error Structure
 */
export interface ValidationError {
  code: ValidationErrorCategory;
  field?: string;
  message: string;
}
