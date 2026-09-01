"""
TrustLedger Synthetic Financial Sandbox Ledger
Phase 7 Bounded Financial Execution Layer
"""

import copy
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class SyntheticFinancialLedger:
    """
    In-memory persistent sandbox financial ledger for synthetic execution.
    Enforces atomic state transitions and rollback on error without touching real money.
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        ctx = context or {}
        self.transactions: Dict[str, Dict[str, Any]] = copy.deepcopy(ctx.get("transactions_db", {}))
        self.orders: Dict[str, Dict[str, Any]] = copy.deepcopy(ctx.get("orders_db", {}))
        self.customers: Dict[str, Dict[str, Any]] = copy.deepcopy(ctx.get("customers_db", {}))
        self.merchants: Dict[str, Dict[str, Any]] = copy.deepcopy(ctx.get("merchants_db", {}))

        self.refund_records: Dict[str, Dict[str, Any]] = {}
        for r in ctx.get("refund_history_db", []):
            r_id = r.get("refund_id") or f"ref_{len(self.refund_records)+1:06d}"
            self.refund_records[r_id] = copy.deepcopy(r)

        self.discount_records: Dict[str, Dict[str, Any]] = {}
        self.payout_records: Dict[str, Dict[str, Any]] = {}
        self.recovery_records: Dict[str, Dict[str, Any]] = {}

        self.counter = 1000

    def _next_ref(self, prefix: str) -> str:
        self.counter += 1
        return f"{prefix}_sync_{self.counter:08d}"

    def apply_refund(
        self,
        txn_id: str,
        cust_id: Optional[str],
        amount_minor: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        txn = self.transactions.get(txn_id)
        if not txn:
            raise KeyError("RECORD_NOT_FOUND: Transaction not found in synthetic ledger.")

        orig_amount_minor = txn.get("amount", {}).get("amount_minor", 0)

        # Calculate previous refunded total for this transaction
        prev_refunded = sum(
            r.get("amount", {}).get("amount_minor", 0)
            for r in self.refund_records.values()
            if r.get("transaction_id") == txn_id and r.get("status") in ["PROCESSED", "SUCCESS"]
        )

        remaining_balance = max(0, orig_amount_minor - prev_refunded)
        if amount_minor > remaining_balance:
            raise ValueError(f"EXCEEDS_REFUNDABLE_BALANCE: Requested refund minor {amount_minor} exceeds remaining balance {remaining_balance}.")

        # Atomically Create Synthetic Refund Record
        ref_id = self._next_ref("ref")
        record = {
            "refund_id": ref_id,
            "transaction_id": txn_id,
            "customer_id": cust_id or txn.get("customer_id"),
            "merchant_id": txn.get("merchant_id"),
            "amount": {"amount_minor": amount_minor, "currency": currency},
            "status": "SUCCESS",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.refund_records[ref_id] = record
        txn["status"] = "REFUNDED" if (prev_refunded + amount_minor >= orig_amount_minor) else "PARTIALLY_REFUNDED"
        return record

    def apply_discount(
        self,
        order_id: Optional[str],
        cust_id: Optional[str],
        amount_minor: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        if order_id and order_id in self.orders:
            order = self.orders[order_id]
            order_amount = order.get("amount", {}).get("amount_minor", 0)
            if amount_minor > order_amount:
                raise ValueError("EXCEEDS_ORDER_AMOUNT: Discount exceeds total order value.")

        disc_id = self._next_ref("disc")
        record = {
            "discount_id": disc_id,
            "order_id": order_id,
            "customer_id": cust_id,
            "amount": {"amount_minor": amount_minor, "currency": currency},
            "status": "SUCCESS",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.discount_records[disc_id] = record
        return record

    def apply_recovery(
        self,
        txn_id: Optional[str],
        cust_id: Optional[str],
        amount_minor: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        rec_id = self._next_ref("rec")
        record = {
            "recovery_id": rec_id,
            "transaction_id": txn_id,
            "customer_id": cust_id,
            "amount": {"amount_minor": amount_minor, "currency": currency},
            "status": "SUCCESS",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.recovery_records[rec_id] = record
        return record

    def apply_payout(
        self,
        merchant_id: str,
        amount_minor: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        payout_id = self._next_ref("payout")
        record = {
            "payout_id": payout_id,
            "merchant_id": merchant_id,
            "amount": {"amount_minor": amount_minor, "currency": currency},
            "status": "SUCCESS",
            "executed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.payout_records[payout_id] = record
        return record
