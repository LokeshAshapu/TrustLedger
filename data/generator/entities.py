"""
TrustLedger Synthetic World Entity Generators
Phase 2 Benchmark Dataset Pipeline
"""

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional

MERCHANT_CATEGORIES = ["ecommerce", "SaaS", "education", "travel", "food", "services"]
CUSTOMER_SEGMENTS = ["REGULAR", "HIGH_VALUE", "NEW", "FREQUENT_RETURNER", "PRICE_SENSITIVE", "INACTIVE"]
PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]
PAYMENT_FAILURE_CODES = [
    "BANK_TIMEOUT",
    "INSUFFICIENT_FUNDS",
    "NETWORK_ERROR",
    "AUTHENTICATION_FAILURE",
    "LIMIT_EXCEEDED",
    "UNKNOWN",
]


class PolicyProfile:
    def __init__(self, policy_profile_id: str, merchant_id: str, rng: random.Random):
        self.policy_profile_id = policy_profile_id
        self.merchant_id = merchant_id
        self.refund_max_automated_minor = rng.choice([1000000, 2500000, 5000000])  # ₹10,000, ₹25,000, ₹50,000
        self.refund_window_days = rng.choice([7, 14, 30])
        self.discount_max_percentage = rng.choice([10.0, 15.0, 25.0])
        self.discount_max_fixed_minor = rng.choice([50000, 100000, 250000])  # ₹500, ₹1,000, ₹2,500
        self.payout_auto_approval_limit_minor = rng.choice([5000000, 10000000, 25000000])  # ₹50,000, ₹100,000, ₹250,000
        self.payment_recovery_max_attempts = rng.choice([2, 3, 5])
        self.effective_from = "2026-01-01T00:00:00Z"
        self.policy_version = "v1.0"

    def to_snapshot_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": "rule_auto_refund_cap",
                "rule_name": "Maximum Automated Refund Cap",
                "threshold_value": self.refund_max_automated_minor,
                "is_hard_constraint": True,
            },
            {
                "rule_id": "rule_refund_window",
                "rule_name": "Eligible Refund Window Days",
                "threshold_value": self.refund_window_days,
                "is_hard_constraint": True,
            },
            {
                "rule_id": "rule_max_discount_pct",
                "rule_name": "Maximum Discount Percentage",
                "threshold_value": self.discount_max_percentage,
                "is_hard_constraint": True,
            },
            {
                "rule_id": "rule_payout_auto_cap",
                "rule_name": "Maximum Automated Payout Cap",
                "threshold_value": self.payout_auto_approval_limit_minor,
                "is_hard_constraint": True,
            },
            {
                "rule_id": "rule_max_recovery_retries",
                "rule_name": "Maximum Payment Recovery Retry Count",
                "threshold_value": self.payment_recovery_max_attempts,
                "is_hard_constraint": True,
            },
        ]


class SyntheticWorld:
    def __init__(self, rng: random.Random, base_time: datetime, time_window_days: int):
        self.rng = rng
        self.base_time = base_time
        self.time_window_days = time_window_days
        self.merchants: Dict[str, Dict[str, Any]] = {}
        self.policy_profiles: Dict[str, PolicyProfile] = {}
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.payment_attempts: Dict[str, Dict[str, Any]] = {}
        self.refund_records: Dict[str, Dict[str, Any]] = {}
        self.discount_records: Dict[str, Dict[str, Any]] = {}
        self.payout_records: Dict[str, Dict[str, Any]] = {}
        self.evidence_records: Dict[str, Dict[str, Any]] = {}

    def generate_world(self, num_merchants: int, num_customers: int):
        # 1. Generate Merchants & Policy Profiles
        for i in range(1, num_merchants + 1):
            merchant_id = f"merch_{i:03d}"
            policy = PolicyProfile(f"pol_{merchant_id}", merchant_id, self.rng)
            self.policy_profiles[merchant_id] = policy

            self.merchants[merchant_id] = {
                "merchant_id": merchant_id,
                "merchant_name": f"Merchant {i:03d} {self.rng.choice(['Corp', 'Tech', 'Stores', 'Labs', 'Pay'])}",
                "category": self.rng.choice(MERCHANT_CATEGORIES),
                "country": "IND",
                "currency": "INR",
                "account_age_days": self.rng.randint(90, 1000),
                "policy_profile_id": policy.policy_profile_id,
            }

        merchant_ids = list(self.merchants.keys())

        # 2. Generate Customers with consistent spend stats
        for i in range(1, num_customers + 1):
            customer_id = f"cust_{i:05d}"
            merchant_id = self.rng.choice(merchant_ids)
            segment = self.rng.choice(CUSTOMER_SEGMENTS)
            age_days = self.rng.randint(10, 500)

            self.customers[customer_id] = {
                "customer_id": customer_id,
                "merchant_id": merchant_id,
                "account_age_days": age_days,
                "customer_segment": segment,
                "total_orders": 0,
                "successful_payments": 0,
                "failed_payments": 0,
                "total_spend_minor": 0,
                "refund_count": 0,
                "refund_amount_minor": 0,
                "discount_count": 0,
                "last_activity_at": (self.base_time - timedelta(days=self.rng.randint(1, self.time_window_days))).isoformat() + "Z",
            }

        # 3. Generate Historical Orders, Transactions & Payments
        self._populate_historical_activity()

    def _populate_historical_activity(self):
        customer_ids = list(self.customers.keys())
        # Generate background activity across timeline
        for idx in range(1, len(customer_ids) * 3 + 1):
            cust_id = self.rng.choice(customer_ids)
            customer = self.customers[cust_id]
            merchant_id = customer["merchant_id"]

            days_ago = self.rng.randint(2, self.time_window_days)
            created_dt = self.base_time - timedelta(days=days_ago, minutes=self.rng.randint(0, 1440))
            created_iso = created_dt.isoformat() + "Z"

            order_id = f"ord_{idx:06d}"
            amount_minor = self.rng.choice([49900, 99900, 149900, 249900, 499900, 999900, 1999900])
            status = self.rng.choice(["FULFILLED", "FULFILLED", "FULFILLED", "CONFIRMED", "CANCELLED"])
            delivery_status = "DELIVERED" if status == "FULFILLED" else ("PENDING" if status == "CONFIRMED" else "NOT_APPLICABLE")

            self.orders[order_id] = {
                "order_id": order_id,
                "merchant_id": merchant_id,
                "customer_id": cust_id,
                "amount": {"amount_minor": amount_minor, "currency": "INR"},
                "status": status,
                "created_at": created_iso,
                "fulfilled_at": (created_dt + timedelta(hours=24)).isoformat() + "Z" if status == "FULFILLED" else None,
                "cancelled_at": (created_dt + timedelta(hours=2)).isoformat() + "Z" if status == "CANCELLED" else None,
                "delivery_status": delivery_status,
            }

            customer["total_orders"] += 1

            if status != "CANCELLED":
                txn_id = f"txn_{idx:06d}"
                payment_method = self.rng.choice(PAYMENT_METHODS)
                txn_status = "CAPTURED" if status == "FULFILLED" else "AUTHORIZED"

                self.transactions[txn_id] = {
                    "transaction_id": txn_id,
                    "order_id": order_id,
                    "merchant_id": merchant_id,
                    "customer_id": cust_id,
                    "amount": {"amount_minor": amount_minor, "currency": "INR"},
                    "payment_method": payment_method,
                    "status": txn_status,
                    "created_at": created_iso,
                    "settled_at": (created_dt + timedelta(minutes=5)).isoformat() + "Z",
                    "reference": f"ref_pay_{idx:06d}",
                }

                customer["successful_payments"] += 1
                customer["total_spend_minor"] += amount_minor

                # Create successful payment attempt
                attempt_id = f"att_{idx:06d}"
                self.payment_attempts[attempt_id] = {
                    "attempt_id": attempt_id,
                    "transaction_id": txn_id,
                    "customer_id": cust_id,
                    "amount": {"amount_minor": amount_minor, "currency": "INR"},
                    "payment_method": payment_method,
                    "status": "SUCCEEDED",
                    "failure_code": None,
                    "attempted_at": created_iso,
                }
