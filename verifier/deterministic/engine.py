"""
TrustLedger Master Deterministic Trust Engine
Phase 3 Deterministic Verification Layer
Engine Version: trustledger.deterministic.v1
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from verifier.deterministic.models import (
    DeterministicVerificationResult,
    Finding,
    FindingSeverity,
    CheckStatus,
    MoneyAmount,
    DETERMINISTIC_ENGINE_VERSION,
)
from verifier.deterministic.schema_validator import SchemaValidator
from evidence_engine.engine import EvidenceEngine
from policy_engine.engine import PolicyEngine
from consistency_engine.engine import ConsistencyEngine


class DeterministicTrustEngine:
    """
    Master Deterministic Trust Engine.
    Executes schema, evidence, policy, and consistency verification pipelines
    without invoking an LLM. Authoritative for hard safety rules.
    """

    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.evidence_engine = EvidenceEngine()
        self.policy_engine = PolicyEngine()
        self.consistency_engine = ConsistencyEngine()

    def verify(self, request: Dict[str, Any], context: Dict[str, Any]) -> DeterministicVerificationResult:
        decision_id = request.get("decision_id", "unknown_decision")

        # Extract observable databases from context
        evidence_db = context.get("evidence_db", {})
        transactions_db = context.get("transactions_db", {})
        orders_db = context.get("orders_db", {})
        customers_db = context.get("customers_db", {})
        merchants_db = context.get("merchants_db", {})
        policy_snapshots_db = context.get("policy_snapshots_db", {})
        refund_history_db = context.get("refund_history_db", [])

        # 1. Schema Validation
        schema_res = self.schema_validator.validate(request)

        # 2. Evidence Validation
        evidence_res = self.evidence_engine.validate(request, evidence_db, transactions_db, orders_db)

        # 3. Policy Evaluation
        policy_res = self.policy_engine.evaluate(request, policy_snapshots_db, transactions_db, orders_db, refund_history_db)

        # 4. Consistency Evaluation
        consistency_res = self.consistency_engine.evaluate(
            request, transactions_db, orders_db, customers_db, merchants_db, evidence_db, refund_history_db
        )

        # Aggregate All Findings
        all_findings: List[Finding] = []
        all_findings.extend(schema_res.findings)
        all_findings.extend(evidence_res.findings)
        all_findings.extend(policy_res.findings)
        all_findings.extend(consistency_res.findings)

        # Categorize Hard Failures vs Warnings
        hard_failures = [f for f in all_findings if f.severity == FindingSeverity.HARD and f.status == CheckStatus.FAIL]
        warnings = [f for f in all_findings if f.severity == FindingSeverity.WARNING]

        # Derived Potential Financial Exposure (safely handled for malformed inputs)
        amount_dict = request.get("amount", {})
        raw_minor = amount_dict.get("amount_minor", 0) if isinstance(amount_dict, dict) else 0
        safe_minor = max(0, int(raw_minor)) if isinstance(raw_minor, (int, float)) and not str(raw_minor).startswith("NaN") else 0
        currency = str(amount_dict.get("currency", "INR")).upper() if isinstance(amount_dict, dict) else "INR"
        if len(currency) != 3:
            currency = "INR"

        potential_exposure = MoneyAmount(amount_minor=safe_minor, currency=currency)

        return DeterministicVerificationResult(
            decision_id=decision_id,
            engine_version=DETERMINISTIC_ENGINE_VERSION,
            schema_result=schema_res,
            evidence_result=evidence_res,
            policy_result=policy_res,
            consistency_result=consistency_res,
            findings=all_findings,
            hard_failures=hard_failures,
            warnings=warnings,
            completed_at=datetime.now(timezone.utc).isoformat(),
            potential_exposure=potential_exposure,
        )
