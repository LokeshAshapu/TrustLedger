import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

import {
  CURRENT_CONTRACT_VERSION,
  LifecycleState,
  ValidationErrorCategory,
} from '../schemas/typescript/contracts.js';
import {
  validateAuditRecord,
  validateConfidence,
  validateDecisionRequest,
  validateEvidence,
  validateExecutionResult,
  validateMoney,
  validateVerificationResult,
} from '../schemas/typescript/validation.js';

const FIXTURES_DIR = path.join(process.cwd(), 'fixtures');

function loadFixture(filename: string) {
  const filePath = path.join(FIXTURES_DIR, filename);
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

describe('TrustLedger Canonical Contract Test Suite', () => {

  describe('1. Valid DecisionRequest Contracts for 4 Action Types', () => {

    it('should validate REFUND action request successfully', () => {
      const payload = loadFixture('refund-valid.json');
      const errors = validateDecisionRequest(payload);
      assert.equal(errors.length, 0, `Unexpected errors: ${JSON.stringify(errors)}`);
    });

    it('should validate DISCOUNT action request successfully', () => {
      const payload = loadFixture('discount-valid.json');
      const errors = validateDecisionRequest(payload);
      assert.equal(errors.length, 0, `Unexpected errors: ${JSON.stringify(errors)}`);
    });

    it('should validate PAYMENT_RECOVERY action request successfully', () => {
      const payload = loadFixture('recovery-valid.json');
      const errors = validateDecisionRequest(payload);
      assert.equal(errors.length, 0, `Unexpected errors: ${JSON.stringify(errors)}`);
    });

    it('should validate PAYOUT action request successfully (without customer_id)', () => {
      const payload = loadFixture('payout-valid.json');
      const errors = validateDecisionRequest(payload);
      assert.equal(errors.length, 0, `Unexpected errors: ${JSON.stringify(errors)}`);
    });

  });

  describe('2. Monetary Representation & Safe Money Rules', () => {

    it('should accept valid Money representation: ₹0 (0 paise)', () => {
      const errors = validateMoney({ amount_minor: 0, currency: 'INR' });
      assert.equal(errors.length, 0);
    });

    it('should accept valid Money representation: ₹1 (100 paise)', () => {
      const errors = validateMoney({ amount_minor: 100, currency: 'INR' });
      assert.equal(errors.length, 0);
    });

    it('should accept valid Money representation: ₹1,499 (149900 paise)', () => {
      const errors = validateMoney({ amount_minor: 149900, currency: 'INR' });
      assert.equal(errors.length, 0);
    });

    it('should accept valid Money representation: Large amounts (₹1,000,000)', () => {
      const errors = validateMoney({ amount_minor: 100000000, currency: 'INR' });
      assert.equal(errors.length, 0);
    });

    it('should reject negative amount_minor values', () => {
      const errors = validateMoney({ amount_minor: -149900, currency: 'INR' });
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_AMOUNT));
    });

    it('should reject decimal floating-point money input', () => {
      const errors = validateMoney({ amount_minor: 1499.50, currency: 'INR' });
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_AMOUNT));
    });

    it('should reject non-uppercase or invalid currency codes', () => {
      const errorsLower = validateMoney({ amount_minor: 100, currency: 'inr' });
      assert.ok(errorsLower.some(e => e.code === ValidationErrorCategory.INVALID_CURRENCY));

      const errorsShort = validateMoney({ amount_minor: 100, currency: 'IN' });
      assert.ok(errorsShort.some(e => e.code === ValidationErrorCategory.INVALID_CURRENCY));
    });

  });

  describe('3. Comprehensive Invalid Input Scenarios', () => {

    it('1. Unknown action type', () => {
      const payload = { ...loadFixture('refund-valid.json'), action_type: 'INVALID_ACTION' };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_ACTION_TYPE));
    });

    it('2. Missing decision_id', () => {
      const payload = { ...loadFixture('refund-valid.json'), decision_id: '' };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD && e.field === 'decision_id'));
    });

    it('3. Missing agent_id', () => {
      const payload = { ...loadFixture('refund-valid.json'), agent_id: '  ' };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD && e.field === 'agent_id'));
    });

    it('4. Negative amount', () => {
      const payload = { ...loadFixture('refund-valid.json'), amount: { amount_minor: -500, currency: 'INR' } };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_AMOUNT));
    });

    it('5. Floating-point money representation', () => {
      const payload = { ...loadFixture('refund-valid.json'), amount: { amount_minor: 149.99, currency: 'INR' } };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_AMOUNT));
    });

    it('6. Invalid currency', () => {
      const payload = { ...loadFixture('refund-valid.json'), amount: { amount_minor: 5000, currency: 'invalid' } };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_CURRENCY));
    });

    it('7. Invalid timestamp', () => {
      const payload = { ...loadFixture('refund-valid.json'), requested_at: '2026-99-99 12:00' };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_TIMESTAMP));
    });

    it('8. Duplicate evidence IDs', () => {
      const payload = loadFixture('duplicate-refund-example.json');
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.DUPLICATE_EVIDENCE_REFERENCE));
    });

    it('9. Invalid verdict in VerificationResult', () => {
      const payload = { ...loadFixture('policy-violation-example.json'), verdict: 'MAYBE' };
      const errors = validateVerificationResult(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_VERDICT));
    });

    it('10. Confidence > 1.0', () => {
      const errors = validateConfidence(1.25);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_CONFIDENCE));
    });

    it('11. Confidence < 0.0', () => {
      const errors = validateConfidence(-0.1);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_CONFIDENCE));
    });

    it('12. Invalid risk level', () => {
      const payload = { ...loadFixture('policy-violation-example.json'), risk_level: 'EXTREME' };
      const errors = validateVerificationResult(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_RISK_LEVEL));
    });

    it('13. Invalid evidence status', () => {
      const payload = {
        contract_version: CURRENT_CONTRACT_VERSION,
        evidence_id: 'ev_101',
        evidence_type: 'ORDER',
        source: 'Shopify',
        source_record_id: 'ord_1',
        timestamp: '2026-08-29T19:00:00Z',
        verification_status: 'UNKNOWN_STATUS',
      };
      const errors = validateEvidence(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_EVIDENCE_STATUS));
    });

    it('14. Invalid execution status', () => {
      const payload = {
        contract_version: CURRENT_CONTRACT_VERSION,
        execution_id: 'exec_101',
        decision_id: 'dec_1',
        status: 'PENDING_FOO',
        provider: 'Razorpay',
        amount: { amount_minor: 1000, currency: 'INR' },
        executed_at: '2026-08-29T19:00:00Z',
        idempotency_key: 'idemp_1',
      };
      const errors = validateExecutionResult(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_EXECUTION_STATUS));
    });

    it('15. Invalid actor type in AuditRecord', () => {
      const payload = {
        contract_version: CURRENT_CONTRACT_VERSION,
        event_id: 'evt_1',
        decision_id: 'dec_1',
        event_type: 'LOG',
        actor_type: 'ROBOT_OVERLORD',
        actor_id: 'act_1',
        timestamp: '2026-08-29T19:00:00Z',
        new_state: LifecycleState.RECEIVED,
        reason: 'test',
        correlation_id: 'corr_1',
      };
      const errors = validateAuditRecord(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_ACTOR_TYPE));
    });

    it('16. Malformed contract version', () => {
      const payload = { ...loadFixture('refund-valid.json'), contract_version: 'trustledger.contract.v999' };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MALFORMED_CONTRACT_VERSION));
    });

  });

  describe('4. Action-Specific Rules', () => {

    it('should reject REFUND without transaction_id', () => {
      const payload = { ...loadFixture('refund-valid.json'), transaction_id: null };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD && e.field === 'transaction_id'));
    });

    it('should reject REFUND without customer_id', () => {
      const payload = { ...loadFixture('refund-valid.json'), customer_id: null };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD && e.field === 'customer_id'));
    });

    it('should reject DISCOUNT without customer_id AND without order_id', () => {
      const payload = { ...loadFixture('discount-valid.json'), customer_id: null, order_id: null };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD));
    });

    it('should accept DISCOUNT with percentage specification', () => {
      const payload = loadFixture('discount-valid.json');
      const errors = validateDecisionRequest(payload);
      assert.equal(errors.length, 0);
    });

    it('should reject DISCOUNT with invalid percentage_points (> 100%)', () => {
      const payload = {
        ...loadFixture('discount-valid.json'),
        discount_spec: { type: 'PERCENTAGE', percentage_points: 150.0 },
      };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.INVALID_DISCOUNT_SPEC));
    });

    it('should reject PAYMENT_RECOVERY without customer_id or transaction_id', () => {
      const payload = { ...loadFixture('recovery-valid.json'), transaction_id: null };
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.some(e => e.code === ValidationErrorCategory.MISSING_REQUIRED_FIELD));
    });

  });

  describe('5. Fixture Validation Integration', () => {

    it('should validate refund-invalid.json fixture with errors', () => {
      const payload = loadFixture('refund-invalid.json');
      const errors = validateDecisionRequest(payload);
      assert.ok(errors.length > 0);
    });

    it('should validate policy-violation-example.json verification result', () => {
      const payload = loadFixture('policy-violation-example.json');
      const errors = validateVerificationResult(payload);
      assert.equal(errors.length, 0);
    });

    it('should validate ambiguous-review-example.json verification result', () => {
      const payload = loadFixture('ambiguous-review-example.json');
      const errors = validateVerificationResult(payload);
      assert.equal(errors.length, 0);
    });

  });

});
