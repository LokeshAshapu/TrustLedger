import {
  ActionType,
  ActorType,
  CURRENT_CONTRACT_VERSION,
  EvidenceType,
  EvidenceVerificationStatus,
  ExecutionStatus,
  LifecycleState,
  ReasonCategory,
  RiskLevel,
  ValidationError,
  ValidationErrorCategory,
  VerdictType,
} from './contracts.js';

const ISO8601_REGEX = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

/**
 * Validates ISO-8601 Timestamp String
 */
export function validateISO8601(timestamp: unknown, fieldName: string): ValidationError[] {
  const errors: ValidationError[] = [];
  if (typeof timestamp !== 'string' || !ISO8601_REGEX.test(timestamp) || Number.isNaN(Date.parse(timestamp))) {
    errors.push({
      code: ValidationErrorCategory.INVALID_TIMESTAMP,
      field: fieldName,
      message: `${fieldName} must be a valid ISO-8601 formatted timestamp string.`,
    });
  }
  return errors;
}

/**
 * Validates Monetary Representation
 */
export function validateMoney(money: unknown, fieldPrefix = 'amount'): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!money || typeof money !== 'object') {
    errors.push({
      code: ValidationErrorCategory.INVALID_AMOUNT,
      field: fieldPrefix,
      message: `${fieldPrefix} must be a valid Money object containing amount_minor and currency.`,
    });
    return errors;
  }

  const m = money as Record<string, unknown>;

  if (typeof m.amount_minor !== 'number' || !Number.isInteger(m.amount_minor) || m.amount_minor < 0) {
    errors.push({
      code: ValidationErrorCategory.INVALID_AMOUNT,
      field: `${fieldPrefix}.amount_minor`,
      message: `${fieldPrefix}.amount_minor must be a non-negative integer representing minor currency units (e.g. paise).`,
    });
  }

  if (typeof m.currency !== 'string' || m.currency.trim() === '' || m.currency !== m.currency.toUpperCase() || m.currency.length !== 3) {
    errors.push({
      code: ValidationErrorCategory.INVALID_CURRENCY,
      field: `${fieldPrefix}.currency`,
      message: `${fieldPrefix}.currency must be a valid 3-letter uppercase ISO currency code (e.g. INR).`,
    });
  }

  return errors;
}

/**
 * Validates Normalized Confidence Score (0.0 - 1.0)
 */
export function validateConfidence(confidence: unknown, fieldName = 'confidence'): ValidationError[] {
  const errors: ValidationError[] = [];
  if (typeof confidence !== 'number' || Number.isNaN(confidence) || confidence < 0.0 || confidence > 1.0) {
    errors.push({
      code: ValidationErrorCategory.INVALID_CONFIDENCE,
      field: fieldName,
      message: `${fieldName} must be a normalized numeric score between 0.0 and 1.0.`,
    });
  }
  return errors;
}

/**
 * Validates Evidence References for Uniqueness and Validity
 */
export function validateEvidenceReferences(refs: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!Array.isArray(refs)) {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'evidence_references',
      message: 'evidence_references must be an array of evidence ID strings.',
    });
    return errors;
  }

  const seen = new Set<string>();
  for (let i = 0; i < refs.length; i++) {
    const ref = refs[i];
    if (typeof ref !== 'string' || ref.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.INVALID_EVIDENCE_REFERENCE,
        field: `evidence_references[${i}]`,
        message: `evidence_references[${i}] must be a non-empty string.`,
      });
      continue;
    }
    if (seen.has(ref)) {
      errors.push({
        code: ValidationErrorCategory.DUPLICATE_EVIDENCE_REFERENCE,
        field: `evidence_references[${i}]`,
        message: `Duplicate evidence reference ID '${ref}' detected.`,
      });
    } else {
      seen.add(ref);
    }
  }

  return errors;
}

/**
 * Validates Canonical DecisionRequest
 */
export function validateDecisionRequest(req: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!req || typeof req !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'DecisionRequest payload must be an object.' }];
  }

  const d = req as Record<string, unknown>;

  // Contract Version
  if (d.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  // decision_id
  if (typeof d.decision_id !== 'string' || d.decision_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'decision_id',
      message: 'decision_id is required and cannot be empty.',
    });
  }

  // action_type
  if (typeof d.action_type !== 'string' || !Object.values(ActionType).includes(d.action_type as ActionType)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_ACTION_TYPE,
      field: 'action_type',
      message: `action_type must be one of: ${Object.values(ActionType).join(', ')}.`,
    });
  }

  // agent_id
  if (typeof d.agent_id !== 'string' || d.agent_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'agent_id',
      message: 'agent_id is required and cannot be empty.',
    });
  }

  // merchant_id
  if (typeof d.merchant_id !== 'string' || d.merchant_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'merchant_id',
      message: 'merchant_id is required and cannot be empty.',
    });
  }

  // amount validation
  errors.push(...validateMoney(d.amount, 'amount'));

  // discount_spec validation (if provided)
  if (d.discount_spec !== undefined && d.discount_spec !== null) {
    const spec = d.discount_spec as Record<string, unknown>;
    if (!spec || typeof spec !== 'object') {
      errors.push({
        code: ValidationErrorCategory.INVALID_DISCOUNT_SPEC,
        field: 'discount_spec',
        message: 'discount_spec must be an object if provided.',
      });
    } else if (spec.type === 'FIXED_AMOUNT') {
      errors.push(...validateMoney(spec.value, 'discount_spec.value'));
    } else if (spec.type === 'PERCENTAGE') {
      if (typeof spec.percentage_points !== 'number' || spec.percentage_points <= 0.0 || spec.percentage_points > 100.0) {
        errors.push({
          code: ValidationErrorCategory.INVALID_DISCOUNT_SPEC,
          field: 'discount_spec.percentage_points',
          message: 'discount_spec.percentage_points must be a number between 0.01 and 100.0.',
        });
      }
    } else {
      errors.push({
        code: ValidationErrorCategory.INVALID_DISCOUNT_SPEC,
        field: 'discount_spec.type',
        message: "discount_spec.type must be 'FIXED_AMOUNT' or 'PERCENTAGE'.",
      });
    }
  }

  // reason validation
  if (!d.reason || typeof d.reason !== 'object') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'reason',
      message: 'reason object containing category is required.',
    });
  } else {
    const r = d.reason as Record<string, unknown>;
    if (typeof r.category !== 'string' || !Object.values(ReasonCategory).includes(r.category as ReasonCategory)) {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'reason.category',
        message: `reason.category must be one of: ${Object.values(ReasonCategory).join(', ')}.`,
      });
    }
  }

  // evidence_references validation
  errors.push(...validateEvidenceReferences(d.evidence_references));

  // requested_at validation
  errors.push(...validateISO8601(d.requested_at, 'requested_at'));

  // Action-specific validation rules
  if (d.action_type === ActionType.REFUND) {
    if (typeof d.customer_id !== 'string' || d.customer_id.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'customer_id',
        message: 'customer_id is required for REFUND actions.',
      });
    }
    if (typeof d.transaction_id !== 'string' || d.transaction_id.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'transaction_id',
        message: 'transaction_id is required for REFUND actions.',
      });
    }
  } else if (d.action_type === ActionType.DISCOUNT) {
    const hasCustomer = typeof d.customer_id === 'string' && d.customer_id.trim() !== '';
    const hasOrder = typeof d.order_id === 'string' && d.order_id.trim() !== '';
    if (!hasCustomer && !hasOrder) {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'customer_id / order_id',
        message: 'DISCOUNT actions require at least customer_id or order_id.',
      });
    }
  } else if (d.action_type === ActionType.PAYMENT_RECOVERY) {
    if (typeof d.customer_id !== 'string' || d.customer_id.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'customer_id',
        message: 'customer_id is required for PAYMENT_RECOVERY actions.',
      });
    }
    if (typeof d.transaction_id !== 'string' || d.transaction_id.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'transaction_id',
        message: 'transaction_id is required for PAYMENT_RECOVERY actions.',
      });
    }
  } else if (d.action_type === ActionType.PAYOUT) {
    if (typeof d.merchant_id !== 'string' || d.merchant_id.trim() === '') {
      errors.push({
        code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
        field: 'merchant_id',
        message: 'merchant_id is required for PAYOUT actions.',
      });
    }
  }

  return errors;
}

/**
 * Validates Evidence Contract Payload
 */
export function validateEvidence(evidence: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!evidence || typeof evidence !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'Evidence payload must be an object.' }];
  }

  const e = evidence as Record<string, unknown>;

  if (e.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  if (typeof e.evidence_id !== 'string' || e.evidence_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'evidence_id',
      message: 'evidence_id is required.',
    });
  }

  if (typeof e.evidence_type !== 'string' || !Object.values(EvidenceType).includes(e.evidence_type as EvidenceType)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_EVIDENCE_STATUS,
      field: 'evidence_type',
      message: `evidence_type must be one of: ${Object.values(EvidenceType).join(', ')}.`,
    });
  }

  if (typeof e.source !== 'string' || e.source.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'source',
      message: 'source provenance is required.',
    });
  }

  if (typeof e.source_record_id !== 'string' || e.source_record_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'source_record_id',
      message: 'source_record_id provenance is required.',
    });
  }

  errors.push(...validateISO8601(e.timestamp, 'timestamp'));

  if (typeof e.verification_status !== 'string' || !Object.values(EvidenceVerificationStatus).includes(e.verification_status as EvidenceVerificationStatus)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_EVIDENCE_STATUS,
      field: 'verification_status',
      message: `verification_status must be one of: ${Object.values(EvidenceVerificationStatus).join(', ')}.`,
    });
  }

  return errors;
}

/**
 * Validates PolicySnapshot Contract Payload
 */
export function validatePolicySnapshot(snapshot: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!snapshot || typeof snapshot !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'PolicySnapshot payload must be an object.' }];
  }

  const p = snapshot as Record<string, unknown>;

  if (p.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  if (typeof p.policy_id !== 'string' || p.policy_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'policy_id',
      message: 'policy_id is required.',
    });
  }

  if (typeof p.merchant_id !== 'string' || p.merchant_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'merchant_id',
      message: 'merchant_id is required.',
    });
  }

  if (typeof p.action_type !== 'string' || !Object.values(ActionType).includes(p.action_type as ActionType)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_ACTION_TYPE,
      field: 'action_type',
      message: `action_type must be one of: ${Object.values(ActionType).join(', ')}.`,
    });
  }

  if (typeof p.policy_version !== 'string' || p.policy_version.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.INVALID_POLICY_VERSION,
      field: 'policy_version',
      message: 'policy_version is required for versioned reproducible policy snapshots.',
    });
  }

  errors.push(...validateISO8601(p.effective_from, 'effective_from'));

  if (!Array.isArray(p.rules)) {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'rules',
      message: 'rules must be an array of policy rule definitions.',
    });
  }

  return errors;
}

/**
 * Validates VerificationResult Contract Payload
 */
export function validateVerificationResult(result: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!result || typeof result !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'VerificationResult payload must be an object.' }];
  }

  const v = result as Record<string, unknown>;

  if (v.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  if (typeof v.decision_id !== 'string' || v.decision_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'decision_id',
      message: 'decision_id is required.',
    });
  }

  if (typeof v.verdict !== 'string' || !Object.values(VerdictType).includes(v.verdict as VerdictType)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_VERDICT,
      field: 'verdict',
      message: `verdict must be one of: ${Object.values(VerdictType).join(', ')}.`,
    });
  }

  errors.push(...validateConfidence(v.confidence, 'confidence'));

  if (typeof v.risk_level !== 'string' || !Object.values(RiskLevel).includes(v.risk_level as RiskLevel)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_RISK_LEVEL,
      field: 'risk_level',
      message: `risk_level must be one of: ${Object.values(RiskLevel).join(', ')}.`,
    });
  }

  errors.push(...validateISO8601(v.verification_started_at, 'verification_started_at'));
  errors.push(...validateISO8601(v.verification_completed_at, 'verification_completed_at'));

  return errors;
}

/**
 * Validates ExecutionResult Contract Payload
 */
export function validateExecutionResult(result: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!result || typeof result !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'ExecutionResult payload must be an object.' }];
  }

  const e = result as Record<string, unknown>;

  if (e.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  if (typeof e.execution_id !== 'string' || e.execution_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'execution_id',
      message: 'execution_id is required.',
    });
  }

  if (typeof e.decision_id !== 'string' || e.decision_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'decision_id',
      message: 'decision_id is required.',
    });
  }

  if (typeof e.status !== 'string' || !Object.values(ExecutionStatus).includes(e.status as ExecutionStatus)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_EXECUTION_STATUS,
      field: 'status',
      message: `status must be one of: ${Object.values(ExecutionStatus).join(', ')}.`,
    });
  }

  errors.push(...validateMoney(e.amount, 'amount'));
  errors.push(...validateISO8601(e.executed_at, 'executed_at'));

  if (typeof e.idempotency_key !== 'string' || e.idempotency_key.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'idempotency_key',
      message: 'idempotency_key is required.',
    });
  }

  return errors;
}

/**
 * Validates AuditRecord Contract Payload
 */
export function validateAuditRecord(record: unknown): ValidationError[] {
  const errors: ValidationError[] = [];
  if (!record || typeof record !== 'object') {
    return [{ code: ValidationErrorCategory.MISSING_REQUIRED_FIELD, message: 'AuditRecord payload must be an object.' }];
  }

  const a = record as Record<string, unknown>;

  if (a.contract_version !== CURRENT_CONTRACT_VERSION) {
    errors.push({
      code: ValidationErrorCategory.MALFORMED_CONTRACT_VERSION,
      field: 'contract_version',
      message: `contract_version must equal '${CURRENT_CONTRACT_VERSION}'.`,
    });
  }

  if (typeof a.event_id !== 'string' || a.event_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'event_id',
      message: 'event_id is required.',
    });
  }

  if (typeof a.decision_id !== 'string' || a.decision_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'decision_id',
      message: 'decision_id is required.',
    });
  }

  if (typeof a.actor_type !== 'string' || !Object.values(ActorType).includes(a.actor_type as ActorType)) {
    errors.push({
      code: ValidationErrorCategory.INVALID_ACTOR_TYPE,
      field: 'actor_type',
      message: `actor_type must be one of: ${Object.values(ActorType).join(', ')}.`,
    });
  }

  if (typeof a.actor_id !== 'string' || a.actor_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'actor_id',
      message: 'actor_id is required.',
    });
  }

  errors.push(...validateISO8601(a.timestamp, 'timestamp'));

  if (typeof a.new_state !== 'string' || !Object.values(LifecycleState).includes(a.new_state as LifecycleState)) {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'new_state',
      message: `new_state must be one of: ${Object.values(LifecycleState).join(', ')}.`,
    });
  }

  if (typeof a.correlation_id !== 'string' || a.correlation_id.trim() === '') {
    errors.push({
      code: ValidationErrorCategory.MISSING_REQUIRED_FIELD,
      field: 'correlation_id',
      message: 'correlation_id is required.',
    });
  }

  return errors;
}
