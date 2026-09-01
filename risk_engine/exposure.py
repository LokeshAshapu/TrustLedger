"""
TrustLedger Financial Risk Exposure Calculator
Phase 4 Deterministic Financial Risk Layer
"""

from typing import Dict, Any, List
from verifier.deterministic.models import MoneyAmount
from risk_engine.models import RiskExposure
from risk_engine.config import RiskConfig


class RiskExposureCalculator:
    """
    Calculates gross exposure, incremental exposure, recoverable amount,
    and irreversible exposure using Phase 1 integer minor units.
    """

    def __init__(self, config: RiskConfig):
        self.config = config

    def calculate(
        self,
        request: Dict[str, Any],
        transactions_db: Dict[str, Dict[str, Any]],
        orders_db: Dict[str, Dict[str, Any]],
        refund_history_db: List[Dict[str, Any]],
    ) -> RiskExposure:
        action_type = request.get("action_type", "REFUND")
        amount_dict = request.get("amount", {})
        currency = str(amount_dict.get("currency", "INR")).upper()

        # Gross Exposure Calculation
        req_amount_minor = max(0, int(amount_dict.get("amount_minor", 0)))
        if action_type == "DISCOUNT" and request.get("discount_spec", {}).get("type") == "PERCENTAGE":
            pct = request.get("discount_spec", {}).get("percentage_points", 0.0)
            order_id = request.get("order_id")
            order = orders_db.get(order_id) if order_id else None
            order_amount_minor = order.get("amount", {}).get("amount_minor", 0) if order else 0
            req_amount_minor = max(0, int((pct / 100.0) * order_amount_minor))

        gross_exp = MoneyAmount(amount_minor=req_amount_minor, currency=currency)

        # Incremental Exposure Calculation (checking remaining balance on transaction)
        txn_id = request.get("transaction_id")
        txn = transactions_db.get(txn_id) if txn_id else None

        incremental_minor = 0
        is_known = True

        if action_type == "REFUND" and txn:
            orig_amount_minor = txn.get("amount", {}).get("amount_minor", 0)
            prev_refunds = [
                r for r in refund_history_db
                if r.get("transaction_id") == txn_id and r.get("status") in ["PROCESSED", "APPROVED"]
            ]
            prev_refunded_minor = sum(r.get("amount", {}).get("amount_minor", 0) for r in prev_refunds)
            remaining_balance_minor = max(0, orig_amount_minor - prev_refunded_minor)

            if req_amount_minor > remaining_balance_minor:
                incremental_minor = req_amount_minor - remaining_balance_minor
        elif not txn and action_type in ["REFUND", "PAYMENT_RECOVERY"]:
            is_known = False

        incremental_exp = MoneyAmount(amount_minor=incremental_minor, currency=currency)

        # Conservative Recoverable Amount Estimation
        recoverable_exp = MoneyAmount(amount_minor=0, currency=currency)

        # Irreversible Exposure Estimation (based on action irreversibility weight)
        irrev_factor = self.config.action_irreversibility.get(action_type, 0.50)
        irreversible_minor = int(req_amount_minor * irrev_factor)
        irreversible_exp = MoneyAmount(amount_minor=irreversible_minor, currency=currency)

        return RiskExposure(
            gross_exposure=gross_exp,
            incremental_exposure=incremental_exp,
            recoverable_amount=recoverable_exp,
            irreversible_exposure=irreversible_exp,
            is_exposure_known=is_known,
        )
