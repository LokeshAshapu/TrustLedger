"""
TrustLedger Deterministic Trust Engine Output Models
Phase 3 Deterministic Verification Layer
Engine Version: trustledger.deterministic.v1
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

DETERMINISTIC_ENGINE_VERSION = "trustledger.deterministic.v1"


class FindingCategory(str, Enum):
    SCHEMA = "SCHEMA"
    EVIDENCE = "EVIDENCE"
    POLICY = "POLICY"
    CONSISTENCY = "CONSISTENCY"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HARD = "HARD"


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Finding(BaseModel):
    check_id: str = Field(min_length=1)
    category: FindingCategory
    severity: FindingSeverity
    status: CheckStatus
    code: str = Field(min_length=1)
    message: str = Field(min_length=1, description="Human-readable explanation of WHAT happened, WHY it matters, and WHAT evidence supports it.")
    evidence_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class ComponentResult(BaseModel):
    status: CheckStatus
    findings: List[Finding] = Field(default_factory=list)


class MoneyAmount(BaseModel):
    amount_minor: int = Field(ge=0)
    currency: str = Field(default="INR")


class DeterministicVerificationResult(BaseModel):
    decision_id: str = Field(min_length=1)
    engine_version: str = Field(default=DETERMINISTIC_ENGINE_VERSION)
    schema_result: ComponentResult
    evidence_result: ComponentResult
    policy_result: ComponentResult
    consistency_result: ComponentResult
    findings: List[Finding] = Field(default_factory=list)
    hard_failures: List[Finding] = Field(default_factory=list)
    warnings: List[Finding] = Field(default_factory=list)
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    potential_exposure: MoneyAmount
