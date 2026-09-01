"""
TrustLedger Financial Risk Engine Output Models
Phase 4 Deterministic Financial Risk Layer
Methodology Version: trustledger.risk.v1
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from verifier.deterministic.models import FindingSeverity, MoneyAmount

RISK_METHODOLOGY_VERSION = "trustledger.risk.v1"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    FINANCIAL = "FINANCIAL"
    POLICY = "POLICY"
    EVIDENCE = "EVIDENCE"
    CONSISTENCY = "CONSISTENCY"
    ACTION = "ACTION"
    TEMPORAL = "TEMPORAL"


class RiskExposure(BaseModel):
    gross_exposure: MoneyAmount
    incremental_exposure: MoneyAmount
    recoverable_amount: MoneyAmount
    irreversible_exposure: MoneyAmount
    is_exposure_known: bool = Field(default=True)


class RiskFactor(BaseModel):
    factor_code: str = Field(min_length=1)
    category: RiskCategory
    contribution: float = Field(ge=0.0, le=1.0, description="Normalized factor risk contribution between 0.0 and 1.0.")
    severity: FindingSeverity
    explanation: str = Field(min_length=1)
    finding_codes: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    decision_id: str = Field(min_length=1)
    risk_level: RiskLevel
    exposure: RiskExposure
    risk_score: float = Field(ge=0.0, le=1.0, description="Normalized TrustLedger risk score strictly between 0.0 and 1.0.")
    factors: List[RiskFactor] = Field(default_factory=list)
    hard_risk_flags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    methodology_version: str = Field(default=RISK_METHODOLOGY_VERSION)
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("risk_score")
    @classmethod
    def validate_score_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"risk_score must be strictly bounded in [0.0, 1.0], got {v}")
        return v
