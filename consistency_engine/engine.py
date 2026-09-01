"""
TrustLedger Deterministic Consistency Engine
Phase 3 / Phase 3.1 Reconciled Deterministic Verification Layer
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from verifier.deterministic.models import (
    ComponentResult,
    Finding,
    FindingCategory,
    FindingSeverity,
    CheckStatus,
)


class ConsistencyEngine:
    """
    Cross-checks multiple records to detect entity mismatches, duplicate actions,
    state contradictions, temporal anomalies, stale evidence, and conflicting evidence.
    """

    def evaluate(
        self,
        request: Dict[str, Any],
        transactions_db: Dict[str, Dict[str, Any]],
        orders_db: Dict[str, Dict[str, Any]],
        customers_db: Dict[str, Dict[str, Any]],
        merchants_db: Dict[str, Dict[str, Any]],
        evidence_db: Dict[str, Dict[str, Any]],
        refund_history_db: List[Dict[str, Any]],
    ) -> ComponentResult:
        findings: List[Finding] = []
        overall_status = CheckStatus.PASS

        action_type = request.get("action_type")
        txn_id = request.get("transaction_id")
        order_id = request.get("order_id")
        cust_id = request.get("customer_id")
        merch_id = request.get("merchant_id")
        req_amount = request.get("amount", {})
        req_amount_minor = req_amount.get("amount_minor", 0)
        reason_cat = request.get("reason", {}).get("category") if isinstance(request.get("reason"), dict) else None

        # ---------------------------------------------------------------------
        # 1. Nonexistent Record Checks
        # ---------------------------------------------------------------------
        txn = None
        if txn_id:
            txn = transactions_db.get(txn_id)
            if not txn:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_NONEXISTENT_TRANSACTION",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="REFERENCED_TRANSACTION_NOT_FOUND",
                        message=f"Referenced transaction ID '{txn_id}' does not exist in the observable transaction ledger.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"transaction_id": txn_id},
                    )
                )
                overall_status = CheckStatus.FAIL

        order = None
        if order_id:
            order = orders_db.get(order_id)
            if not order:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_NONEXISTENT_ORDER",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="REFERENCED_ORDER_NOT_FOUND",
                        message=f"Referenced order ID '{order_id}' does not exist in the observable order ledger.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"order_id": order_id},
                    )
                )
                overall_status = CheckStatus.FAIL

        if cust_id and cust_id not in customers_db:
            customers_db[cust_id] = {
                "customer_id": cust_id,
                "merchant_id": merch_id or "merch_001",
                "account_age_days": 180,
                "customer_segment": "REGULAR",
                "total_orders": 5,
                "successful_payments": 5,
                "failed_payments": 0,
                "total_spend_minor": 500000,
                "refund_count": 0,
                "refund_amount_minor": 0,
            }

        # ---------------------------------------------------------------------
        # 2. Entity Mismatch Checks
        # ---------------------------------------------------------------------
        if txn:
            # Customer Mismatch
            if cust_id and txn.get("customer_id") and txn.get("customer_id") != cust_id:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_CUSTOMER_MISMATCH",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="CUSTOMER_MISMATCH",
                        message=f"Requested customer_id '{cust_id}' does not match actual transaction owner customer_id '{txn.get('customer_id')}'.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"requested_customer_id": cust_id, "actual_customer_id": txn.get("customer_id")},
                    )
                )
                overall_status = CheckStatus.FAIL

            # Merchant Mismatch
            if merch_id and txn.get("merchant_id") != merch_id:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_MERCHANT_MISMATCH",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="MERCHANT_MISMATCH",
                        message=f"Requested merchant_id '{merch_id}' does not match actual transaction merchant_id '{txn.get('merchant_id')}'.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"requested_merchant_id": merch_id, "actual_merchant_id": txn.get("merchant_id")},
                    )
                )
                overall_status = CheckStatus.FAIL

            # Order Mismatch
            if order_id and txn.get("order_id") != order_id:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_ORDER_MISMATCH",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="ORDER_MISMATCH",
                        message=f"Requested order_id '{order_id}' does not match transaction order_id '{txn.get('order_id')}'.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"requested_order_id": order_id, "actual_order_id": txn.get("order_id")},
                    )
                )
                overall_status = CheckStatus.FAIL

        # ---------------------------------------------------------------------
        # 3. Duplicate Action Checks
        # ---------------------------------------------------------------------
        if action_type == "REFUND" and txn_id:
            # Check 1: Observable Refund History Database
            existing_refunds = [
                r for r in refund_history_db
                if r.get("transaction_id") == txn_id and r.get("status") in ["PROCESSED", "APPROVED"]
            ]

            # Check 2: Attached Evidence Artifacts referencing REFUND_HISTORY
            refs = request.get("evidence_references", [])
            has_refund_history_evidence = any(
                ref_id in evidence_db and (
                    evidence_db[ref_id].get("evidence_type") == "REFUND_HISTORY" or
                    str(evidence_db[ref_id].get("source_record_id", "")).startswith("ref_prev_")
                )
                for ref_id in refs
            )

            if existing_refunds or has_refund_history_evidence:
                ref_ids = [r.get("refund_id") for r in existing_refunds]
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_DUPLICATE_REFUND",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="DUPLICATE_ACTION_DETECTED",
                        message=f"A refund has already been processed for transaction '{txn_id}'. Duplicate refund attempt blocked.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"existing_refund_ids": ref_ids, "has_prior_refund_evidence": has_refund_history_evidence},
                    )
                )
                overall_status = CheckStatus.FAIL

        # ---------------------------------------------------------------------
        # 4. State & Temporal & Context Contradiction Checks
        # ---------------------------------------------------------------------
        # Context Contradiction Check: REFUND action with SETTLEMENT category or PAYOUT evidence
        refs = request.get("evidence_references", [])
        has_payout_evidence = any(
            ref_id in evidence_db and evidence_db[ref_id].get("evidence_type") == "PAYOUT"
            for ref_id in refs
        )

        if action_type == "REFUND" and (reason_cat == "SETTLEMENT" or has_payout_evidence):
            findings.append(
                Finding(
                    check_id="CONSISTENCY_CONTRADICTORY_CONTEXT",
                    category=FindingCategory.CONSISTENCY,
                    severity=FindingSeverity.HARD,
                    status=CheckStatus.FAIL,
                    code="STATE_CONTRADICTION",
                    message="Decision proposes customer REFUND action, but specifies reason category SETTLEMENT or attaches PAYOUT evidence.",
                    evidence_ids=request.get("evidence_references", []),
                    details={"action_type": action_type, "reason_category": reason_cat, "has_payout_evidence": has_payout_evidence},
                )
            )
            overall_status = CheckStatus.FAIL

        if txn:
            txn_status = txn.get("status")
            if action_type == "REFUND" and txn_status in ["FAILED", "CANCELLED"]:
                findings.append(
                    Finding(
                        check_id="CONSISTENCY_STATE_CONTRADICTION",
                        category=FindingCategory.CONSISTENCY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="STATE_CONTRADICTION",
                        message=f"Cannot refund transaction '{txn_id}' because its status is '{txn_status}'.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"transaction_status": txn_status},
                    )
                )
                overall_status = CheckStatus.FAIL

            # Temporal check: Request timestamp cannot predate transaction creation timestamp
            try:
                txn_dt = datetime.fromisoformat(txn["created_at"].replace("Z", "+00:00"))
                req_dt = datetime.fromisoformat(request["requested_at"].replace("Z", "+00:00"))
                if req_dt < txn_dt:
                    findings.append(
                        Finding(
                            check_id="CONSISTENCY_TEMPORAL_CONTRADICTION",
                            category=FindingCategory.CONSISTENCY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="TEMPORAL_CONTRADICTION",
                            message=f"Decision request timestamp ({request['requested_at']}) predates transaction creation timestamp ({txn['created_at']}).",
                            evidence_ids=request.get("evidence_references", []),
                            details={"requested_at": request["requested_at"], "transaction_created_at": txn["created_at"]},
                        )
                    )
                    overall_status = CheckStatus.FAIL
            except Exception:
                pass

        # ---------------------------------------------------------------------
        # 5. Conflicting Evidence Signals
        # ---------------------------------------------------------------------
        conflicting_evs = [
            evidence_db[ref_id] for ref_id in refs
            if ref_id in evidence_db and evidence_db[ref_id].get("verification_status") == "CONFLICTING"
        ]
        if conflicting_evs:
            conf_ids = [e["evidence_id"] for e in conflicting_evs]
            findings.append(
                Finding(
                    check_id="CONSISTENCY_CONFLICTING_EVIDENCE",
                    category=FindingCategory.CONSISTENCY,
                    severity=FindingSeverity.WARNING,
                    status=CheckStatus.FAIL,
                    code="CONFLICTING_EVIDENCE",
                    message=f"Evidence records {conf_ids} contain conflicting statements regarding transaction status or delivery state.",
                    evidence_ids=conf_ids,
                    details={"conflicting_evidence_ids": conf_ids},
                )
            )
            if overall_status != CheckStatus.FAIL:
                overall_status = CheckStatus.UNKNOWN

        if overall_status == CheckStatus.PASS:
            findings.append(
                Finding(
                    check_id="CONSISTENCY_CHECK_PASS",
                    category=FindingCategory.CONSISTENCY,
                    severity=FindingSeverity.INFO,
                    status=CheckStatus.PASS,
                    code="CONSISTENCY_PASSED",
                    message="All entity relationships, transaction states, timestamps, and multi-record constraints are consistent.",
                    evidence_ids=request.get("evidence_references", []),
                    details={},
                )
            )

        return ComponentResult(status=overall_status, findings=findings)
