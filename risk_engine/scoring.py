"""
TrustLedger Deterministic Risk Scorer
Phase 4 Deterministic Financial Risk Layer
"""

from typing import Dict, Any, List, Tuple
from verifier.deterministic.models import DeterministicVerificationResult, FindingSeverity, CheckStatus
from risk_engine.models import RiskExposure, RiskFactor, RiskCategory, RiskLevel
from risk_engine.config import RiskConfig


class RiskScorer:
    """
    Computes a normalized risk score between 0.0 and 1.0, generates structured risk factors,
    evaluates hard risk flags, and maps the score to a RiskLevel (LOW, MEDIUM, HIGH, CRITICAL).
    """

    def __init__(self, config: RiskConfig):
        self.config = config

    def score(
        self,
        request: Dict[str, Any],
        exposure: RiskExposure,
        det_result: DeterministicVerificationResult,
    ) -> Tuple[float, RiskLevel, List[RiskFactor], List[str], List[str]]:
        factors: List[RiskFactor] = []
        hard_risk_flags: List[str] = []
        warnings: List[str] = []

        action_type = request.get("action_type", "REFUND")
        gross_minor = exposure.gross_exposure.amount_minor

        # ---------------------------------------------------------------------
        # 1. Financial Exposure Band Score
        # ---------------------------------------------------------------------
        if gross_minor < self.config.low_max_minor:
            exposure_score = 0.10
            exp_band_code = "LOW_MONETARY_EXPOSURE"
            exp_severity = FindingSeverity.INFO
        elif gross_minor < self.config.medium_max_minor:
            exposure_score = 0.30
            exp_band_code = "MEDIUM_MONETARY_EXPOSURE"
            exp_severity = FindingSeverity.INFO
        elif gross_minor < self.config.high_max_minor:
            exposure_score = 0.60
            exp_band_code = "HIGH_MONETARY_EXPOSURE"
            exp_severity = FindingSeverity.WARNING
            hard_risk_flags.append("HIGH_FINANCIAL_EXPOSURE")
        else:
            exposure_score = 0.90
            exp_band_code = "CRITICAL_MONETARY_EXPOSURE"
            exp_severity = FindingSeverity.HARD
            hard_risk_flags.append("HIGH_FINANCIAL_EXPOSURE")

        gross_inr = gross_minor / 100.0
        factors.append(
            RiskFactor(
                factor_code=exp_band_code,
                category=RiskCategory.FINANCIAL,
                contribution=exposure_score,
                severity=exp_severity,
                explanation=f"Proposed financial action exposes INR {gross_inr:,.2f}.",
                finding_codes=[],
            )
        )

        # Incremental Exposure Penalty
        if exposure.incremental_exposure.amount_minor > 0:
            inc_inr = exposure.incremental_exposure.amount_minor / 100.0
            exposure_score = min(1.0, exposure_score + 0.20)
            factors.append(
                RiskFactor(
                    factor_code="INCREMENTAL_EXPOSURE_EXCESS",
                    category=RiskCategory.FINANCIAL,
                    contribution=0.20,
                    severity=FindingSeverity.HARD,
                    explanation=f"Proposed action attempts INR {inc_inr:,.2f} excess exposure beyond valid remaining balance.",
                    finding_codes=["REFUND_EXCEEDS_REMAINING_BALANCE"],
                )
            )

        # ---------------------------------------------------------------------
        # 2. Action Type Severity & Irreversibility Score
        # ---------------------------------------------------------------------
        action_weight = self.config.action_weights.get(action_type, 0.60)
        action_irrev = self.config.action_irreversibility.get(action_type, 0.50)
        action_score = action_weight * action_irrev

        if action_irrev >= 0.80:
            hard_risk_flags.append("IRREVERSIBLE_ACTION")

        factors.append(
            RiskFactor(
                factor_code="ACTION_TYPE_IRREVERSIBILITY",
                category=RiskCategory.ACTION,
                contribution=action_score,
                severity=FindingSeverity.WARNING if action_irrev >= 0.5 else FindingSeverity.INFO,
                explanation=f"Action type '{action_type}' has an irreversibility rating of {action_irrev:.2f}.",
                finding_codes=[],
            )
        )

        # ---------------------------------------------------------------------
        # 3. Deterministic Findings Score
        # ---------------------------------------------------------------------
        hard_findings = det_result.hard_failures
        warning_findings = det_result.warnings

        hard_count = len(hard_findings)
        warning_count = len(warning_findings)

        hard_score = min(1.0, hard_count * self.config.finding_weights["HARD"])
        warning_score = min(0.5, warning_count * self.config.finding_weights["WARNING"])
        findings_score = min(1.0, hard_score + warning_score)

        if hard_count >= 2:
            hard_risk_flags.append("MULTIPLE_HARD_FINDINGS")

        for f in hard_findings:
            if f.code in ["REFUND_LIMIT_EXCEEDED", "MAX_DISCOUNT_PERCENTAGE_EXCEEDED", "PAYOUT_LIMIT_EXCEEDED"]:
                if "POLICY_BREACH" not in hard_risk_flags:
                    hard_risk_flags.append("POLICY_BREACH")
            elif f.code == "DUPLICATE_ACTION_DETECTED":
                if "DUPLICATE_FINANCIAL_ACTION" not in hard_risk_flags:
                    hard_risk_flags.append("DUPLICATE_FINANCIAL_ACTION")
            elif f.code in ["CUSTOMER_MISMATCH", "MERCHANT_MISMATCH", "ORDER_MISMATCH"]:
                if "ENTITY_MISMATCH" not in hard_risk_flags:
                    hard_risk_flags.append("ENTITY_MISMATCH")

            factors.append(
                RiskFactor(
                    factor_code=f"DETERMINISTIC_HARD_{f.code}",
                    category=RiskCategory.POLICY if f.category == "POLICY" else (RiskCategory.CONSISTENCY if f.category == "CONSISTENCY" else RiskCategory.FINANCIAL),
                    contribution=self.config.finding_weights["HARD"],
                    severity=FindingSeverity.HARD,
                    explanation=f.message,
                    finding_codes=[f.code],
                )
            )

        for w in warning_findings:
            if w.code in ["EVIDENCE_STATUS_MISSING", "NO_EVIDENCE_ATTACHED"]:
                if "MISSING_CRITICAL_EVIDENCE" not in hard_risk_flags:
                    hard_risk_flags.append("MISSING_CRITICAL_EVIDENCE")
            elif w.code in ["CONFLICTING_EVIDENCE_STATUS", "CONFLICTING_EVIDENCE"]:
                if "CONFLICTING_EVIDENCE" not in hard_risk_flags:
                    hard_risk_flags.append("CONFLICTING_EVIDENCE")

            factors.append(
                RiskFactor(
                    factor_code=f"DETERMINISTIC_WARNING_{w.code}",
                    category=RiskCategory.EVIDENCE if w.category == "EVIDENCE" else RiskCategory.CONSISTENCY,
                    contribution=self.config.finding_weights["WARNING"],
                    severity=FindingSeverity.WARNING,
                    explanation=w.message,
                    finding_codes=[w.code],
                )
            )

        # ---------------------------------------------------------------------
        # 4. Uncertainty Score
        # ---------------------------------------------------------------------
        uncertainty_score = 0.0
        if not exposure.is_exposure_known:
            uncertainty_score = 0.60
            warnings.append("Financial state or underlying transaction is unverified; exposure calculation is uncertain.")
            factors.append(
                RiskFactor(
                    factor_code="EXPOSURE_STATE_UNKNOWN",
                    category=RiskCategory.EVIDENCE,
                    contribution=0.60,
                    severity=FindingSeverity.WARNING,
                    explanation="Underlying transaction state is unknown or unverified.",
                    finding_codes=["REFERENCED_TRANSACTION_NOT_FOUND"],
                )
            )

        # ---------------------------------------------------------------------
        # 5. Composite Normalized Risk Score Formula
        # ---------------------------------------------------------------------
        raw_score = (
            (0.40 * exposure_score) +
            (0.40 * findings_score) +
            (0.15 * action_score) +
            (0.05 * uncertainty_score)
        )

        final_score = round(min(1.0, max(0.0, raw_score)), 4)

        # ---------------------------------------------------------------------
        # 6. Map Score to RiskLevel
        # ---------------------------------------------------------------------
        if final_score < self.config.low_upper:
            risk_level = RiskLevel.LOW
        elif final_score < self.config.medium_upper:
            risk_level = RiskLevel.MEDIUM
        elif final_score < self.config.high_upper:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        # Deduplicate flags while preserving order
        unique_flags = list(dict.fromkeys(hard_risk_flags))

        return final_score, risk_level, factors, unique_flags, warnings
