"""
TrustLedger Schema Validator Integration
Phase 3 Deterministic Verification Layer
"""

from typing import Dict, Any, List
from verifier.contracts import DecisionRequest
from verifier.deterministic.models import (
    ComponentResult,
    Finding,
    FindingCategory,
    FindingSeverity,
    CheckStatus,
)


class SchemaValidator:
    """
    Invokes Phase 1 Canonical Contract Validation.
    Generates HARD FAIL findings for malformed request payloads.
    """

    def validate(self, raw_payload: Dict[str, Any]) -> ComponentResult:
        findings: List[Finding] = []

        try:
            # Invoke Phase 1 Pydantic Contract Validation
            DecisionRequest.model_validate(raw_payload)

            findings.append(
                Finding(
                    check_id="SCHEMA_CONTRACT_VALIDATION",
                    category=FindingCategory.SCHEMA,
                    severity=FindingSeverity.INFO,
                    status=CheckStatus.PASS,
                    code="SCHEMA_VALID",
                    message="Payload strictly satisfies canonical Phase 1 DecisionRequest schema contract.",
                    evidence_ids=[],
                    details={},
                )
            )
            return ComponentResult(status=CheckStatus.PASS, findings=findings)

        except Exception as e:
            findings.append(
                Finding(
                    check_id="SCHEMA_CONTRACT_VALIDATION",
                    category=FindingCategory.SCHEMA,
                    severity=FindingSeverity.HARD,
                    status=CheckStatus.FAIL,
                    code="MALFORMED_DECISION_REQUEST",
                    message=f"Payload failed canonical Phase 1 schema validation: {str(e)}",
                    evidence_ids=[],
                    details={"error": str(e)},
                )
            )
            return ComponentResult(status=CheckStatus.FAIL, findings=findings)
