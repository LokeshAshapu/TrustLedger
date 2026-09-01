"""
TrustLedger AI Contextual Verification Engine Output & Packet Models
Phase 5 AI Contextual Verification Layer
Verifier Version: trustledger.ai-verifier.v1
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from verifier.deterministic.models import DeterministicVerificationResult
from risk_engine.models import RiskAssessment

AI_VERIFIER_VERSION = "trustledger.ai-verifier.v1"


class AIRecommendation(str, Enum):
    SUPPORT = "SUPPORT"
    UNCERTAIN = "UNCERTAIN"
    CONTRADICT = "CONTRADICT"


class AIVerificationPacket(BaseModel):
    decision: Dict[str, Any]
    relevant_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    related_records: Dict[str, Any] = Field(default_factory=dict)
    policy_snapshot: Dict[str, Any] = Field(default_factory=dict)
    deterministic_result: Dict[str, Any]
    risk_assessment: Dict[str, Any]


class ReasoningFactor(BaseModel):
    factor: str = Field(min_length=1)
    category: str = Field(min_length=1)
    assessment: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    evidence_ids: List[str] = Field(default_factory=list)


class ContradictoryEvidenceItem(BaseModel):
    evidence_id: str = Field(min_length=1)
    issue: str = Field(min_length=1)
    impact: str = Field(min_length=1)


class DeterministicConflictItem(BaseModel):
    finding_code: str = Field(min_length=1)
    acknowledged: bool = Field(default=True)
    explanation: str = Field(min_length=1)


class AIVerificationResult(BaseModel):
    model_config = {"protected_namespaces": ()}

    decision_id: str = Field(min_length=1)

    recommendation: AIRecommendation
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence in its contextual assessment strictly between 0.0 and 1.0.")
    contextual_assessment: str = Field(min_length=1)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[ContradictoryEvidenceItem] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    reasoning_factors: List[ReasoningFactor] = Field(default_factory=list)
    deterministic_conflicts: List[DeterministicConflictItem] = Field(default_factory=list)
    model_id: str = Field(min_length=1)
    verifier_version: str = Field(default=AI_VERIFIER_VERSION)
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("confidence")
    @classmethod
    def validate_confidence_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence must be strictly bounded in [0.0, 1.0], got {v}")
        return v
