"""
TrustLedger — Python Compatibility Models
Contract Version: trustledger.contract.v1

Pydantic v2 representations of the canonical TrustLedger contracts.
Matches TypeScript definitions and JSON Schemas 1:1.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

CURRENT_CONTRACT_VERSION = "trustledger.contract.v1"


class ActionType(str, Enum):
    REFUND = "REFUND"
    DISCOUNT = "DISCOUNT"
    PAYMENT_RECOVERY = "PAYMENT_RECOVERY"
    PAYOUT = "PAYOUT"


class VerdictType(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class LifecycleState(str, Enum):
    RECEIVED = "RECEIVED"
    NORMALIZED = "NORMALIZED"
    EVIDENCE_CHECK = "EVIDENCE_CHECK"
    POLICY_CHECK = "POLICY_CHECK"
    CONSISTENCY_CHECK = "CONSISTENCY_CHECK"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    AI_VERIFICATION = "AI_VERIFICATION"
    VERDICT = "VERDICT"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    BLOCKED = "BLOCKED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ReasonCategory(str, Enum):
    DUPLICATE_PAYMENT = "DUPLICATE_PAYMENT"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    NON_DELIVERY = "NON_DELIVERY"
    SERVICE_FAILURE = "SERVICE_FAILURE"
    PROMOTIONAL_DISCOUNT = "PROMOTIONAL_DISCOUNT"
    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    SETTLEMENT = "SETTLEMENT"
    OTHER = "OTHER"


class EvidenceType(str, Enum):
    TRANSACTION = "TRANSACTION"
    ORDER = "ORDER"
    PAYMENT_ATTEMPT = "PAYMENT_ATTEMPT"
    REFUND_HISTORY = "REFUND_HISTORY"
    CUSTOMER_HISTORY = "CUSTOMER_HISTORY"
    POLICY = "POLICY"
    INVOICE = "INVOICE"
    PAYOUT = "PAYOUT"
    DELIVERY = "DELIVERY"
    OTHER = "OTHER"


class EvidenceVerificationStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    CONFLICTING = "CONFLICTING"
    MISSING = "MISSING"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ActorType(str, Enum):
    AI_AGENT = "AI_AGENT"
    TRUSTLEDGER = "TRUSTLEDGER"
    HUMAN = "HUMAN"
    FINANCIAL_SYSTEM = "FINANCIAL_SYSTEM"


class Money(BaseModel):
    amount_minor: int = Field(ge=0, description="Integer minor unit (e.g. paise for INR)")
    currency: str = Field(pattern=r"^[A-Z]{3}$", description="ISO 4217 uppercase currency code")


class ReasonSpec(BaseModel):
    category: ReasonCategory
    explanation: Optional[str] = None


class FixedDiscountSpec(BaseModel):
    type: str = Field(default="FIXED_AMOUNT")
    value: Money


class PercentageDiscountSpec(BaseModel):
    type: str = Field(default="PERCENTAGE")
    percentage_points: float = Field(gt=0.0, le=100.0)


DiscountSpec = Union[FixedDiscountSpec, PercentageDiscountSpec]


class DecisionRequest(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    decision_id: str = Field(min_length=1)
    action_type: ActionType
    agent_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    customer_id: Optional[str] = None
    transaction_id: Optional[str] = None
    order_id: Optional[str] = None
    amount: Money
    discount_spec: Optional[DiscountSpec] = None
    reason: ReasonSpec
    evidence_references: List[str]
    requested_at: str
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("evidence_references")
    @classmethod
    def validate_unique_evidence_refs(cls, refs: List[str]) -> List[str]:
        if len(refs) != len(set(refs)):
            raise ValueError("Duplicate evidence_references detected.")
        return refs


class Evidence(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    evidence_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    source: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    timestamp: str
    content_hash: Optional[str] = None
    verification_status: EvidenceVerificationStatus
    metadata: Optional[Dict[str, Any]] = None


class PolicyRule(BaseModel):
    rule_id: str = Field(min_length=1)
    rule_name: str = Field(min_length=1)
    description: Optional[str] = None
    threshold_value: Optional[Any] = None
    is_hard_constraint: bool


class PolicySnapshot(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    policy_id: str = Field(min_length=1)
    merchant_id: str = Field(min_length=1)
    action_type: ActionType
    rules: List[PolicyRule]
    effective_from: str
    effective_until: Optional[str] = None
    policy_version: str = Field(min_length=1)


class EvidenceResult(BaseModel):
    evidence_score: float = Field(ge=0.0, le=1.0)
    verified_count: int = Field(ge=0)
    missing_references: List[str]


class PolicyViolation(BaseModel):
    policy_id: str
    rule_id: str
    message: str


class PolicyResult(BaseModel):
    passed: bool
    violations: List[PolicyViolation]


class ConsistencyResult(BaseModel):
    is_consistent: bool
    contradictions: List[str]


class AIResult(BaseModel):
    verdict_recommendation: VerdictType
    reasoning_summary: str
    detected_risk_factors: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class VerificationResult(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    decision_id: str = Field(min_length=1)
    verdict: VerdictType
    confidence: float = Field(ge=0.0, le=1.0, description="Normalized model confidence signal, not absolute truth.")
    risk_level: RiskLevel
    evidence_result: EvidenceResult
    policy_result: PolicyResult
    consistency_result: ConsistencyResult
    ai_result: AIResult
    reasons: List[str]
    missing_evidence: List[str]
    verification_started_at: str
    verification_completed_at: str
    verifier_version: str = Field(min_length=1)


class ExecutionResult(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    execution_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    status: ExecutionStatus
    provider: str = Field(min_length=1)
    provider_reference: Optional[str] = None
    amount: Money
    executed_at: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    idempotency_key: str = Field(min_length=1)


class AuditRecord(BaseModel):
    contract_version: str = Field(default=CURRENT_CONTRACT_VERSION)
    event_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    actor_type: ActorType
    actor_id: str = Field(min_length=1)
    timestamp: str
    previous_state: Optional[LifecycleState] = None
    new_state: LifecycleState
    reason: str
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: str = Field(min_length=1)
