"""
TrustLedger Synthetic World Data Repository
Phase 10A End-to-End Backend Orchestration
Data Boundary: Reads exclusively from data/processed/. NEVER reads data/ground-truth/.
"""

import json
import os
from typing import Dict, Any, List


class SyntheticDataRepository:
    """
    Repository for loading and indexing observable financial data from data/processed/.
    Strictly isolated from hidden ground-truth labels.
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data", "processed")

        self.data_dir = data_dir
        self.evidence_db: Dict[str, Dict[str, Any]] = {}
        self.transactions_db: Dict[str, Dict[str, Any]] = {}
        self.orders_db: Dict[str, Dict[str, Any]] = {}
        self.customers_db: Dict[str, Dict[str, Any]] = {}
        self.merchants_db: Dict[str, Dict[str, Any]] = {}
        self.policy_snapshots_db: Dict[str, Dict[str, Any]] = {}
        self.refund_history_db: List[Dict[str, Any]] = []

        self._load_data()

    def _load_data(self):
        if not os.path.exists(self.data_dir):
            return

        # Load Evidence
        ev_path = os.path.join(self.data_dir, "evidence.jsonl")
        if os.path.exists(ev_path):
            with open(ev_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        ev_id = item.get("evidence_id")
                        if ev_id:
                            self.evidence_db[ev_id] = item

        # Load Transactions
        tx_path = os.path.join(self.data_dir, "transactions.jsonl")
        if os.path.exists(tx_path):
            with open(tx_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        tx_id = item.get("transaction_id")
                        if tx_id:
                            self.transactions_db[tx_id] = item

        # Load Orders
        ord_path = os.path.join(self.data_dir, "orders.jsonl")
        if os.path.exists(ord_path):
            with open(ord_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        ord_id = item.get("order_id")
                        if ord_id:
                            self.orders_db[ord_id] = item

        # Load Customers
        cust_path = os.path.join(self.data_dir, "customers.jsonl")
        if os.path.exists(cust_path):
            with open(cust_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        cust_id = item.get("customer_id")
                        if cust_id:
                            self.customers_db[cust_id] = item

        # Load Policies
        pol_path = os.path.join(self.data_dir, "policies.jsonl")
        if os.path.exists(pol_path):
            with open(pol_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        merch_id = item.get("merchant_id")
                        if merch_id:
                            self.policy_snapshots_db[merch_id] = item

        # Load Refund History
        ref_path = os.path.join(self.data_dir, "refunds.jsonl")
        if os.path.exists(ref_path):
            with open(ref_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        self.refund_history_db.append(item)

    def get_context_for_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds observable database context for a given request.
        Allows in-memory augmentation if request passes inline context objects.
        """
        req_context = request.get("context", {})

        merged_evidence = {**self.evidence_db, **req_context.get("evidence_db", {})}
        merged_transactions = {**self.transactions_db, **req_context.get("transactions_db", {})}
        merged_orders = {**self.orders_db, **req_context.get("orders_db", {})}
        merged_customers = {**self.customers_db, **req_context.get("customers_db", {})}
        merged_merchants = {**self.merchants_db, **req_context.get("merchants_db", {})}
        merged_policies = {**self.policy_snapshots_db, **req_context.get("policy_snapshots_db", {})}
        merged_refunds = list(self.refund_history_db) + req_context.get("refund_history_db", [])

        return {
            "evidence_db": merged_evidence,
            "transactions_db": merged_transactions,
            "orders_db": merged_orders,
            "customers_db": merged_customers,
            "merchants_db": merged_merchants,
            "policy_snapshots_db": merged_policies,
            "refund_history_db": merged_refunds,
        }
