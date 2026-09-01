"""
TrustLedger Bounded Financial Execution Simulator & Razorpay Integration Models
Phase 11B.2 ExecutionGateway -> Razorpay Test Mode
Simulator Version: trustledger.execution-simulator.v1
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from verifier.deterministic.models import MoneyAmount

EXECUTION_SIMULATOR_VERSION = "trustledger.execution-simulator.v1"


class AuthorizationStatus(str, Enum):
    ISSUED = "ISSUED"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


class ExecutionStatus(str, Enum):
    EXECUTED = "EXECUTED"
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    AUTHORIZATION_INVALID = "AUTHORIZATION_INVALID"
    AUTHORIZATION_EXPIRED = "AUTHORIZATION_EXPIRED"
    AUTHORIZATION_ALREADY_CONSUMED = "AUTHORIZATION_ALREADY_CONSUMED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_CONFLICT = "PROVIDER_CONFLICT"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class FailureCode(str, Enum):
    NONE = "NONE"
    AUTHORIZATION_NOT_FOUND = "AUTHORIZATION_NOT_FOUND"
    AUTHORIZATION_EXPIRED = "AUTHORIZATION_EXPIRED"
    AUTHORIZATION_ALREADY_USED = "AUTHORIZATION_ALREADY_USED"
    AUTHORIZATION_ALREADY_CONSUMED = "AUTHORIZATION_ALREADY_CONSUMED"
    AUTHORIZATION_REVOKED = "AUTHORIZATION_REVOKED"
    DECISION_HASH_MISMATCH = "DECISION_HASH_MISMATCH"
    DECISION_NOT_APPROVED = "DECISION_NOT_APPROVED"
    ACTION_MISMATCH = "ACTION_MISMATCH"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    PAYMENT_ID_MISMATCH = "PAYMENT_ID_MISMATCH"
    INVALID_AUTHORIZATION = "INVALID_AUTHORIZATION"
    EXCEEDS_REFUNDABLE_BALANCE = "EXCEEDS_REFUNDABLE_BALANCE"
    RECORD_NOT_FOUND = "RECORD_NOT_FOUND"
    SIMULATED_LEDGER_ERROR = "SIMULATED_LEDGER_ERROR"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_CONFLICT = "PROVIDER_CONFLICT"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    PROVIDER_AUTH_ERROR = "PROVIDER_AUTH_ERROR"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"


class ExecutionAuthorization(BaseModel):
    authorization_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    decision_hash: str = Field(min_length=64, max_length=64)
    action_type: str = Field(min_length=1)
    authorized_amount: MoneyAmount
    issued_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = Field(min_length=1)
    status: AuthorizationStatus = Field(default=AuthorizationStatus.ISSUED)


class ExecutionResult(BaseModel):
    execution_id: str = Field(min_length=1)
    authorization_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    status: ExecutionStatus
    action_type: str = Field(min_length=1)
    amount: MoneyAmount
    external_reference: Optional[str] = Field(default=None)
    failure_code: FailureCode = Field(default=FailureCode.NONE)
    executed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    idempotency_key: Optional[str] = Field(default=None)
    provider: str = Field(default="trustledger_simulator")
    provider_environment: str = Field(default="test")
    refund_id: Optional[str] = Field(default=None)
    payment_id: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)


class ExecutionAuditRecord(BaseModel):
    audit_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    authorization_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    amount_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    status: ExecutionStatus
    failure_code: FailureCode
    decision_hash: str = Field(min_length=64, max_length=64)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    provider: str = Field(default="trustledger_simulator")
    provider_environment: str = Field(default="test")
    refund_id: Optional[str] = Field(default=None)
    payment_id: Optional[str] = Field(default=None)
