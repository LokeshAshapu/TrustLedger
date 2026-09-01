"""
TrustLedger Deterministic Policy Engine
Phase 3 Deterministic Verification Layer
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from verifier.deterministic.models import (
    ComponentResult,
    Finding,
    FindingCategory,
    FindingSeverity,
    CheckStatus,
)


class PolicyEngine:
    """
    Evaluates deterministic business & safety rules using versioned PolicySnapshots.
    Deterministic rules have absolute authority over LLM outputs.
    """

    def evaluate(
        self,
        request: Dict[str, Any],
        policy_snapshots_db: Dict[str, Dict[str, Any]],
        transactions_db: Dict[str, Dict[str, Any]],
        orders_db: Dict[str, Dict[str, Any]],
        refund_history_db: List[Dict[str, Any]],
    ) -> ComponentResult:
        findings: List[Finding] = []
        merch_id = request.get("merchant_id")
        action_type = request.get("action_type")
        amount = request.get("amount", {})
        req_amount_minor = amount.get("amount_minor", 0)

        snapshot = policy_snapshots_db.get(merch_id)
        if not snapshot:
            findings.append(
                Finding(
                    check_id="POLICY_SNAPSHOT_CHECK",
                    category=FindingCategory.POLICY,
                    severity=FindingSeverity.WARNING,
                    status=CheckStatus.UNKNOWN,
                    code="NO_POLICY_SNAPSHOT_FOUND",
                    message=f"No policy snapshot found for merchant '{merch_id}'. Defaulting policy evaluation status to UNKNOWN.",
                    evidence_ids=[],
                    details={"merchant_id": merch_id},
                )
            )
            return ComponentResult(status=CheckStatus.UNKNOWN, findings=findings)

        rules = {r["rule_id"]: r for r in snapshot.get("rules", [])}
        overall_status = CheckStatus.PASS

        # ---------------------------------------------------------------------
        # 1. REFUND Policy Rules
        # ---------------------------------------------------------------------
        if action_type == "REFUND":
            # Rule: Max Automated Refund Cap
            rule_cap = rules.get("rule_auto_refund_cap")
            if rule_cap and rule_cap.get("threshold_value"):
                cap_minor = int(rule_cap["threshold_value"])
                if req_amount_minor > cap_minor:
                    req_inr = req_amount_minor / 100.0
                    cap_inr = cap_minor / 100.0
                    findings.append(
                        Finding(
                            check_id="POLICY_REFUND_AUTOMATED_CAP",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="REFUND_LIMIT_EXCEEDED",
                            message=f"Requested refund of INR {req_inr:,.2f} exceeds merchant's automated refund cap of INR {cap_inr:,.2f}.",
                            evidence_ids=request.get("evidence_references", []),
                            details={"requested_amount_minor": req_amount_minor, "cap_minor": cap_minor},
                        )
                    )
                    overall_status = CheckStatus.FAIL

            # Rule: Refund Window Days
            txn_id = request.get("transaction_id")
            txn = transactions_db.get(txn_id) if txn_id else None
            rule_window = rules.get("rule_refund_window")

            if txn and rule_window and rule_window.get("threshold_value"):
                window_days = int(rule_window["threshold_value"])
                try:
                    txn_dt = datetime.fromisoformat(txn["created_at"].replace("Z", "+00:00"))
                    req_dt = datetime.fromisoformat(request["requested_at"].replace("Z", "+00:00"))
                    days_elapsed = (req_dt - txn_dt).days
                    if days_elapsed > window_days:
                        findings.append(
                            Finding(
                                check_id="POLICY_REFUND_WINDOW_CHECK",
                                category=FindingCategory.POLICY,
                                severity=FindingSeverity.HARD,
                                status=CheckStatus.FAIL,
                                code="REFUND_WINDOW_EXPIRED",
                                message=f"Refund request created {days_elapsed} days after transaction, exceeding allowed window of {window_days} days.",
                                evidence_ids=request.get("evidence_references", []),
                                details={"days_elapsed": days_elapsed, "window_days": window_days},
                            )
                        )
                        overall_status = CheckStatus.FAIL
                except Exception:
                    pass

            # Rule: Refund Cannot Exceed Original Transaction Amount
            if txn:
                orig_amount_minor = txn.get("amount", {}).get("amount_minor", 0)
                if req_amount_minor > orig_amount_minor:
                    req_inr = req_amount_minor / 100.0
                    orig_inr = orig_amount_minor / 100.0
                    findings.append(
                        Finding(
                            check_id="POLICY_REFUND_EXCEEDS_TRANSACTION",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="REFUND_EXCEEDS_TRANSACTION",
                            message=f"Requested refund of INR {req_inr:,.2f} exceeds original transaction amount of INR {orig_inr:,.2f}.",
                            evidence_ids=request.get("evidence_references", []),
                            details={"requested_amount_minor": req_amount_minor, "original_amount_minor": orig_amount_minor},
                        )
                    )
                    overall_status = CheckStatus.FAIL

                # Rule: Previously Refunded + Requested Cannot Exceed Captured Amount
                prev_refunds = [
                    r for r in refund_history_db
                    if r.get("transaction_id") == txn_id and r.get("status") in ["PROCESSED", "APPROVED"]
                ]
                prev_refunded_minor = sum(r.get("amount", {}).get("amount_minor", 0) for r in prev_refunds)

                if prev_refunded_minor + req_amount_minor > orig_amount_minor:
                    total_inr = (prev_refunded_minor + req_amount_minor) / 100.0
                    orig_inr = orig_amount_minor / 100.0
                    findings.append(
                        Finding(
                            check_id="POLICY_REFUND_EXCEEDS_REMAINING_BALANCE",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="REFUND_EXCEEDS_REMAINING_BALANCE",
                            message=f"Total refunded amount INR {total_inr:,.2f} (previously refunded INR {prev_refunded_minor/100:,.2f} + requested INR {req_amount_minor/100:,.2f}) exceeds original transaction amount of INR {orig_inr:,.2f}.",
                            evidence_ids=request.get("evidence_references", []),
                            details={
                                "previously_refunded_minor": prev_refunded_minor,
                                "requested_amount_minor": req_amount_minor,
                                "original_amount_minor": orig_amount_minor,
                            },
                        )
                    )
                    overall_status = CheckStatus.FAIL

        # ---------------------------------------------------------------------
        # 2. DISCOUNT Policy Rules
        # ---------------------------------------------------------------------
        elif action_type == "DISCOUNT":
            rule_disc_pct = rules.get("rule_max_discount_pct")
            discount_spec = request.get("discount_spec")

            if discount_spec and discount_spec.get("type") == "PERCENTAGE":
                pct = discount_spec.get("percentage_points", 0.0)
                max_pct = float(rule_disc_pct.get("threshold_value", 15.0)) if rule_disc_pct else 15.0
                if pct > max_pct:
                    findings.append(
                        Finding(
                            check_id="POLICY_DISCOUNT_MAX_PERCENTAGE",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="MAX_DISCOUNT_PERCENTAGE_EXCEEDED",
                            message=f"Proposed discount of {pct}% exceeds maximum allowed policy cap of {max_pct}%.",
                            evidence_ids=request.get("evidence_references", []),
                            details={"proposed_percentage": pct, "max_percentage": max_pct},
                        )
                    )
                    overall_status = CheckStatus.FAIL

            order_id = request.get("order_id")
            order = orders_db.get(order_id) if order_id else None
            if order:
                order_amount_minor = order.get("amount", {}).get("amount_minor", 0)
                if req_amount_minor > order_amount_minor:
                    findings.append(
                        Finding(
                            check_id="POLICY_DISCOUNT_EXCEEDS_ORDER",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="DISCOUNT_EXCEEDS_ORDER_VALUE",
                            message=f"Proposed discount of INR {req_amount_minor/100:,.2f} exceeds order value of INR {order_amount_minor/100:,.2f}.",
                            evidence_ids=request.get("evidence_references", []),
                            details={"requested_discount_minor": req_amount_minor, "order_amount_minor": order_amount_minor},
                        )
                    )
                    overall_status = CheckStatus.FAIL

        # ---------------------------------------------------------------------
        # 3. PAYMENT_RECOVERY Policy Rules
        # ---------------------------------------------------------------------
        elif action_type == "PAYMENT_RECOVERY":
            rule_retries = rules.get("rule_max_recovery_retries")
            metadata = request.get("metadata", {}) or {}
            retry_count = metadata.get("retry_attempt", 1)

            if rule_retries and rule_retries.get("threshold_value"):
                max_retries = int(rule_retries["threshold_value"])
                if retry_count > max_retries:
                    findings.append(
                        Finding(
                            check_id="POLICY_RECOVERY_MAX_RETRIES",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="MAX_RECOVERY_RETRIES_EXCEEDED",
                            message=f"Requested payment recovery retry count ({retry_count}) exceeds merchant maximum policy retry limit ({max_retries}).",
                            evidence_ids=request.get("evidence_references", []),
                            details={"retry_attempt": retry_count, "max_retries": max_retries},
                        )
                    )
                    overall_status = CheckStatus.FAIL

            txn_id = request.get("transaction_id")
            txn = transactions_db.get(txn_id) if txn_id else None
            if txn and txn.get("status") in ["CAPTURED", "AUTHORIZED"]:
                findings.append(
                    Finding(
                        check_id="POLICY_RECOVERY_ALREADY_SUCCESSFUL",
                        category=FindingCategory.POLICY,
                        severity=FindingSeverity.HARD,
                        status=CheckStatus.FAIL,
                        code="PAYMENT_ALREADY_SUCCESSFUL",
                        message=f"Cannot initiate payment recovery for transaction '{txn_id}' which is already in '{txn.get('status')}' state.",
                        evidence_ids=request.get("evidence_references", []),
                        details={"transaction_status": txn.get("status")},
                    )
                )
                overall_status = CheckStatus.FAIL

        # ---------------------------------------------------------------------
        # 4. PAYOUT Policy Rules
        # ---------------------------------------------------------------------
        elif action_type == "PAYOUT":
            rule_payout_cap = rules.get("rule_payout_auto_cap")
            if rule_payout_cap and rule_payout_cap.get("threshold_value"):
                payout_cap = int(rule_payout_cap["threshold_value"])
                if req_amount_minor > payout_cap:
                    findings.append(
                        Finding(
                            check_id="POLICY_PAYOUT_AUTOMATED_CAP",
                            category=FindingCategory.POLICY,
                            severity=FindingSeverity.HARD,
                            status=CheckStatus.FAIL,
                            code="PAYOUT_LIMIT_EXCEEDED",
                            message=f"Requested payout of INR {req_amount_minor/100:,.2f} exceeds merchant automated payout cap of INR {payout_cap/100:,.2f}.",
                            evidence_ids=request.get("evidence_references", []),
                            details={"requested_payout_minor": req_amount_minor, "payout_cap_minor": payout_cap},
                        )
                    )
                    overall_status = CheckStatus.FAIL

        if overall_status == CheckStatus.PASS:
            findings.append(
                Finding(
                    check_id="POLICY_EVALUATION_PASS",
                    category=FindingCategory.POLICY,
                    severity=FindingSeverity.INFO,
                    status=CheckStatus.PASS,
                    code="POLICY_RULES_PASSED",
                    message=f"Decision request satisfies all deterministic policy snapshot rules for merchant '{merch_id}'.",
                    evidence_ids=request.get("evidence_references", []),
                    details={"policy_version": snapshot.get("policy_version")},
                )
            )

        return ComponentResult(status=overall_status, findings=findings)
