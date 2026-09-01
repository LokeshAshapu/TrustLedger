"""
TrustLedger Decision Gate Models & Canonical Contracts
Phase 6 Signal Aggregation & Decision Layer
Gate Version: trustledger.decision-gate.v1
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

GATE_VERSION = "trustledger.decision-gate.v1"


class FinalVerdict(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class EvidenceQualityState(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"


class PrimaryReason(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ReviewerQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    question_text: str = Field(min_length=1)
    context_snippet: Optional[str] = Field(default=None)


class ReviewContext(BaseModel):
    decision_id: str = Field(min_length=1)
    proposed_action: str = Field(min_length=1)
    risk_summary: Dict[str, Any] = Field(default_factory=dict)
    deterministic_findings_summary: List[str] = Field(default_factory=list)
    ai_assessment_summary: Optional[str] = Field(default=None)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradictory_evidence_items: List[Dict[str, Any]] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)
    reviewer_questions: List[ReviewerQuestion] = Field(default_factory=list)


class StageTrace(BaseModel):
    stage_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    input_summary: str = Field(min_length=1)
    output_summary: str = Field(min_length=1)
    rule_id: Optional[str] = Field(default=None)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionResult(BaseModel):
    decision_id: str = Field(min_length=1)
    verdict: FinalVerdict
    decision_rule: str = Field(min_length=1, description="Rule ID that rendered the final verdict, e.g. TL-DG-002")
    primary_reason: PrimaryReason
    contributing_findings: List[str] = Field(default_factory=list)
    risk_level: str = Field(min_length=1)
    risk_score: float = Field(ge=0.0, le=1.0)
    ai_recommendation: str = Field(default="NONE")
    evidence_state: EvidenceQualityState
    review_context: Optional[ReviewContext] = Field(default=None)
    decision_trace: List[StageTrace] = Field(default_factory=list)
    decision_hash: str = Field(min_length=64, max_length=64, description="SHA-256 canonical hash of decision payload")
    gate_version: str = Field(default=GATE_VERSION)
    decided_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ExecutionAuthorization(BaseModel):
    """
    Placeholder schema for future Phase 7 execution authorization.
    ONLY verdict == APPROVE decisions are eligible for authorization.
    """
    decision_id: str = Field(min_length=1)
    verdict: FinalVerdict = Field(default=FinalVerdict.APPROVE)
    authorization_id: str = Field(min_length=1)
    expires_at: str = Field(min_length=1)
    decision_hash: str = Field(min_length=64, max_length=64)
