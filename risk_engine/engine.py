"""
TrustLedger Master Deterministic Financial Risk Engine
Phase 4 Deterministic Financial Risk Layer
Methodology Version: trustledger.risk.v1
"""

from typing import Dict, Any
from datetime import datetime, timezone

from verifier.deterministic.models import DeterministicVerificationResult
from risk_engine.models import RiskAssessment, RISK_METHODOLOGY_VERSION
from risk_engine.config import RiskConfig
from risk_engine.exposure import RiskExposureCalculator
from risk_engine.scoring import RiskScorer


class FinancialRiskEngine:
    """
    Master Financial Risk Engine.
    Evaluates financial exposure, action irreversibility, policy breaches,
    and deterministic findings to calculate a normalized risk score and RiskAssessment
    without invoking an LLM or accessing hidden ground-truth labels.
    """

    def __init__(self, config_path: str = None):
        self.config = RiskConfig(config_path) if config_path else RiskConfig()
        self.exposure_calculator = RiskExposureCalculator(self.config)
        self.scorer = RiskScorer(self.config)

    def assess(
        self,
        request: Dict[str, Any],
        context: Dict[str, Any],
        det_result: DeterministicVerificationResult,
    ) -> RiskAssessment:
        decision_id = request.get("decision_id", "unknown_decision")

        transactions_db = context.get("transactions_db", {})
        orders_db = context.get("orders_db", {})
        refund_history_db = context.get("refund_history_db", [])

        # 1. Calculate Financial Exposure
        exposure = self.exposure_calculator.calculate(
            request, transactions_db, orders_db, refund_history_db
        )

        # 2. Compute Deterministic Risk Score, Level, Factors, and Hard Flags
        risk_score, risk_level, factors, hard_flags, warnings = self.scorer.score(
            request, exposure, det_result
        )

        return RiskAssessment(
            decision_id=decision_id,
            risk_level=risk_level,
            exposure=exposure,
            risk_score=risk_score,
            factors=factors,
            hard_risk_flags=hard_flags,
            warnings=warnings,
            methodology_version=RISK_METHODOLOGY_VERSION,
            assessed_at=datetime.now(timezone.utc).isoformat(),
        )
