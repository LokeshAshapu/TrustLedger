"""
TrustLedger Master Execution Gateway
Phase 11B.2 ExecutionGateway -> Razorpay Test Mode
Simulator Version: trustledger.execution-simulator.v1
"""

import copy
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from verifier.deterministic.models import MoneyAmount
from decision_gate.models import DecisionResult, FinalVerdict
from decision_gate.hashing import compute_decision_hash
from execution_engine.models import (
    ExecutionAuthorization,
    ExecutionResult,
    ExecutionStatus,
    AuthorizationStatus,
    FailureCode,
    ExecutionAuditRecord,
    EXECUTION_SIMULATOR_VERSION,
)
from execution_engine.config import ExecutionConfig
from execution_engine.ledger import SyntheticFinancialLedger

from execution.razorpay_client import RazorpayTestClient
from execution.models import RefundRequest as RazorpayRefundRequest
from execution.errors import (
    RazorpayClientError,
    RazorpayAuthenticationError,
    RazorpayValidationError,
    RazorpayNotFoundError,
    RazorpayConflictError,
    RazorpayRateLimitError,
    RazorpayServerError,
    RazorpayTimeoutError,
    RazorpayNetworkError,
)


class ExecutionGateway:
    """
    Master Execution Gateway & Sandbox Financial Simulator.
    Enforces strict non-bypass financial execution boundaries, decision hash validation,
    single-use replay protection, tamper detection, TTL expiration, idempotency, and atomic execution.
    Integrates with RazorpayTestClient for test-mode execution when action == REFUND and verdict == APPROVE.
    """

    def __init__(
        self,
        context: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        razorpay_client: Optional[RazorpayTestClient] = None,
    ):
        self.config = ExecutionConfig(config_path) if config_path else ExecutionConfig()
        self.ledger = SyntheticFinancialLedger(context)
        self.razorpay_client = razorpay_client or RazorpayTestClient()

        self.authorizations: Dict[str, ExecutionAuthorization] = {}
        self.execution_results: Dict[str, ExecutionResult] = {}
        self.idempotency_map: Dict[str, ExecutionResult] = {}
        self.audit_records: List[ExecutionAuditRecord] = []

    # -------------------------------------------------------------------------
    # 1. Authorization Issuance (ONLY verdict == APPROVE decisions allowed!)
    # -------------------------------------------------------------------------
    def authorize(self, decision_result: DecisionResult) -> ExecutionAuthorization:
        if decision_result.verdict != FinalVerdict.APPROVE:
            raise ValueError(
                f"DECISION_NOT_APPROVED: Cannot issue execution authorization for verdict '{decision_result.verdict.value}'. "
                "Only APPROVE decisions are eligible."
            )

        auth_id = f"auth_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=self.config.authorization_ttl_seconds)).isoformat()

        # Extract Action Type & Amount from decision trace or canonical attributes
        action_type = "REFUND"
        for trace_stage in decision_result.decision_trace:
            if trace_stage.stage_name == "CONTRACT" and "Action: " in trace_stage.input_summary:
                action_type = trace_stage.input_summary.split("Action: ")[1].split(",")[0].strip()
                break

        # Reconstruct Authorized Money Amount
        gross_minor = 0
        for trace_stage in decision_result.decision_trace:
            if trace_stage.stage_name == "RISK_ASSESSMENT" and "Gross Exposure: " in trace_stage.input_summary:
                gross_minor = int(trace_stage.input_summary.split("Gross Exposure: ")[1].split(" ")[0].strip())
                break

        authorized_money = MoneyAmount(amount_minor=gross_minor, currency="INR")

        auth = ExecutionAuthorization(
            authorization_id=auth_id,
            decision_id=decision_result.decision_id,
            decision_hash=decision_result.decision_hash,
            action_type=action_type,
            authorized_amount=authorized_money,
            issued_at=now.isoformat(),
            expires_at=expires_at,
            status=AuthorizationStatus.ISSUED,
        )

        self.authorizations[auth_id] = auth
        return auth

    # -------------------------------------------------------------------------
    # 2. Execution Gateway (Enforces All Security Controls Before Execution)
    # -------------------------------------------------------------------------
    def execute(
        self,
        authorization_id: str,
        decision_result: DecisionResult,
        request: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        override_now: Optional[datetime] = None,
        use_razorpay: bool = False,
    ) -> ExecutionResult:

        now = override_now or datetime.now(timezone.utc)
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"

        # 1. Idempotency Check
        effective_idempotency_key = idempotency_key or request.get("idempotency_key")
        if effective_idempotency_key and effective_idempotency_key in self.idempotency_map:
            return self.idempotency_map[effective_idempotency_key]

        # Helper to construct failure result
        def _make_failure(
            code: FailureCode,
            status: ExecutionStatus = ExecutionStatus.REJECTED,
            error_code: Optional[str] = None,
            provider: str = "trustledger_gateway",
        ) -> ExecutionResult:
            res = ExecutionResult(
                execution_id=exec_id,
                authorization_id=authorization_id,
                decision_id=decision_result.decision_id if decision_result else "unknown",
                status=status,
                action_type=request.get("action_type", "UNKNOWN"),
                amount=MoneyAmount(
                    amount_minor=request.get("amount", {}).get("amount_minor", 0),
                    currency=request.get("amount", {}).get("currency", "INR"),
                ),
                external_reference=None,
                failure_code=code,
                executed_at=now.isoformat(),
                idempotency_key=effective_idempotency_key,
                provider=provider,
                provider_environment="test",
                payment_id=request.get("payment_id") or request.get("transaction_id"),
                error_code=error_code or code.value,
            )
            self._log_audit(res, decision_result.decision_hash if decision_result else "0" * 64)
            if effective_idempotency_key:
                self.idempotency_map[effective_idempotency_key] = res
            return res

        # 2. Decision Result Existence & Verdict Check
        if not decision_result:
            return _make_failure(FailureCode.AUTHORIZATION_NOT_FOUND, status=ExecutionStatus.REJECTED)

        if decision_result.verdict != FinalVerdict.APPROVE:
            return _make_failure(FailureCode.DECISION_NOT_APPROVED, status=ExecutionStatus.DENIED)

        # 3. Authorization Existence Check
        auth = self.authorizations.get(authorization_id)
        if not auth:
            return _make_failure(FailureCode.AUTHORIZATION_NOT_FOUND, status=ExecutionStatus.REJECTED)

        # 4. Single-Use Replay Protection Check
        if auth.status == AuthorizationStatus.USED:
            return _make_failure(FailureCode.AUTHORIZATION_ALREADY_USED, status=ExecutionStatus.REJECTED)

        if auth.status != AuthorizationStatus.ISSUED:
            return _make_failure(FailureCode.AUTHORIZATION_REVOKED, status=ExecutionStatus.REJECTED)

        # 5. Authorization Decision ID Binding Check
        if auth.decision_id != decision_result.decision_id:
            return _make_failure(FailureCode.INVALID_AUTHORIZATION, status=ExecutionStatus.REJECTED)

        # 6. TTL Expiration Check
        exp_dt = datetime.fromisoformat(auth.expires_at)
        if now > exp_dt:
            auth.status = AuthorizationStatus.EXPIRED
            return _make_failure(FailureCode.AUTHORIZATION_EXPIRED, status=ExecutionStatus.REJECTED)

        # 7. Decision Hash Validation
        recomputed_hash = compute_decision_hash(decision_result.model_dump())
        if recomputed_hash != auth.decision_hash or decision_result.decision_hash != auth.decision_hash:
            return _make_failure(FailureCode.DECISION_HASH_MISMATCH, status=ExecutionStatus.REJECTED)

        # 8. Tamper Protection Checks (Action, Amount, Currency)
        req_action = request.get("action_type")
        req_amount = request.get("amount", {})
        req_minor = req_amount.get("amount_minor", 0)
        req_currency = str(req_amount.get("currency", "INR")).upper()

        if req_action != auth.action_type:
            return _make_failure(FailureCode.ACTION_MISMATCH, status=ExecutionStatus.REJECTED)

        if req_minor != auth.authorized_amount.amount_minor:
            return _make_failure(FailureCode.AMOUNT_MISMATCH, status=ExecutionStatus.REJECTED)

        if req_currency != auth.authorized_amount.currency:
            return _make_failure(FailureCode.CURRENCY_MISMATCH, status=ExecutionStatus.REJECTED)

        payment_id = request.get("payment_id") or request.get("transaction_id") or "pay_simulated_001"

        # 9. PROVIDER CALL BOUNDARY (ONLY REACHED IF ALL 12 AUTHORIZATION CHECKS PASS!)
        if req_action == "REFUND" and use_razorpay:
            idempotency = effective_idempotency_key or f"idempotency_{auth.authorization_id[:16]}"
            try:
                rzp_req = RazorpayRefundRequest(
                    payment_id=payment_id,
                    amount_minor=req_minor,
                    currency=req_currency,
                    idempotency_key=idempotency,
                    receipt=request.get("receipt"),
                    notes=request.get("notes") or {},
                )

                # SINGLE OBVIOUS PROVIDER CALL LOCATION
                rzp_res = self.razorpay_client.create_refund(rzp_req)

                # Successful execution -> transition authorization status to USED
                auth.status = AuthorizationStatus.USED

                res = ExecutionResult(
                    execution_id=exec_id,
                    authorization_id=authorization_id,
                    decision_id=decision_result.decision_id,
                    status=ExecutionStatus.EXECUTED,
                    action_type=req_action,
                    amount=MoneyAmount(amount_minor=req_minor, currency=req_currency),
                    external_reference=rzp_res.refund_id,
                    failure_code=FailureCode.NONE,
                    executed_at=now.isoformat(),
                    idempotency_key=idempotency,
                    provider="razorpay",
                    provider_environment="test",
                    refund_id=rzp_res.refund_id,
                    payment_id=rzp_res.payment_id,
                )

                self.execution_results[exec_id] = res
                if effective_idempotency_key:
                    self.idempotency_map[effective_idempotency_key] = res
                self._log_audit(res, auth.decision_hash)

                return res

            except RazorpayConflictError as ex:
                return _make_failure(
                    FailureCode.PROVIDER_CONFLICT,
                    status=ExecutionStatus.PROVIDER_CONFLICT,
                    error_code="PROVIDER_CONFLICT",
                    provider="razorpay",
                )
            except RazorpayRateLimitError as ex:
                return _make_failure(
                    FailureCode.PROVIDER_RATE_LIMIT,
                    status=ExecutionStatus.PROVIDER_RATE_LIMIT,
                    error_code="PROVIDER_RATE_LIMIT",
                    provider="razorpay",
                )
            except RazorpayTimeoutError as ex:
                return _make_failure(
                    FailureCode.PROVIDER_TIMEOUT,
                    status=ExecutionStatus.PROVIDER_TIMEOUT,
                    error_code="PROVIDER_TIMEOUT",
                    provider="razorpay",
                )
            except (RazorpayServerError, RazorpayNetworkError) as ex:
                return _make_failure(
                    FailureCode.PROVIDER_ERROR,
                    status=ExecutionStatus.PROVIDER_ERROR,
                    error_code="PROVIDER_ERROR",
                    provider="razorpay",
                )
            except RazorpayAuthenticationError as ex:
                return _make_failure(
                    FailureCode.PROVIDER_AUTH_ERROR,
                    status=ExecutionStatus.FAILED,
                    error_code="AUTHENTICATION_ERROR",
                    provider="razorpay",
                )
            except RazorpayNotFoundError as ex:
                return _make_failure(
                    FailureCode.PROVIDER_NOT_FOUND,
                    status=ExecutionStatus.FAILED,
                    error_code="NOT_FOUND_ERROR",
                    provider="razorpay",
                )
            except RazorpayClientError as ex:
                return _make_failure(
                    FailureCode.SIMULATED_LEDGER_ERROR,
                    status=ExecutionStatus.FAILED,
                    error_code=ex.error_code,
                    provider="razorpay",
                )

        # Fallback for synthetic simulator execution for non-REFUND actions or when use_razorpay is False
        try:
            if req_action == "REFUND":
                rec = self.ledger.apply_refund(
                    txn_id=payment_id,
                    cust_id=request.get("customer_id"),
                    amount_minor=req_minor,
                    currency=req_currency,
                )
                ext_ref = rec["refund_id"]

            elif req_action == "DISCOUNT":
                rec = self.ledger.apply_discount(
                    order_id=request.get("order_id"),
                    cust_id=request.get("customer_id"),
                    amount_minor=req_minor,
                    currency=req_currency,
                )
                ext_ref = rec["discount_id"]

            elif req_action == "PAYMENT_RECOVERY":
                rec = self.ledger.apply_recovery(
                    txn_id=payment_id,
                    cust_id=request.get("customer_id"),
                    amount_minor=req_minor,
                    currency=req_currency,
                )
                ext_ref = rec["recovery_id"]

            elif req_action == "PAYOUT":
                rec = self.ledger.apply_payout(
                    merchant_id=request.get("merchant_id"),
                    amount_minor=req_minor,
                    currency=req_currency,
                )
                ext_ref = rec["payout_id"]
            else:
                return _make_failure(FailureCode.ACTION_MISMATCH, status=ExecutionStatus.REJECTED)

        except KeyError:
            return _make_failure(FailureCode.RECORD_NOT_FOUND, status=ExecutionStatus.FAILED)
        except ValueError as ve:
            if "EXCEEDS_REFUNDABLE_BALANCE" in str(ve):
                return _make_failure(FailureCode.EXCEEDS_REFUNDABLE_BALANCE, status=ExecutionStatus.FAILED)
            return _make_failure(FailureCode.SIMULATED_LEDGER_ERROR, status=ExecutionStatus.FAILED)
        except Exception:
            return _make_failure(FailureCode.SIMULATED_LEDGER_ERROR, status=ExecutionStatus.FAILED)

        # Mark Authorization as USED upon successful state transition
        auth.status = AuthorizationStatus.USED

        res = ExecutionResult(
            execution_id=exec_id,
            authorization_id=authorization_id,
            decision_id=decision_result.decision_id,
            status=ExecutionStatus.SUCCESS,
            action_type=req_action,
            amount=MoneyAmount(amount_minor=req_minor, currency=req_currency),
            external_reference=ext_ref,
            failure_code=FailureCode.NONE,
            executed_at=now.isoformat(),
            idempotency_key=effective_idempotency_key,
            provider="trustledger_simulator",
            provider_environment="test",
            refund_id=ext_ref,
            payment_id=payment_id,
        )

        self.execution_results[exec_id] = res
        if effective_idempotency_key:
            self.idempotency_map[effective_idempotency_key] = res
        self._log_audit(res, auth.decision_hash)

        return res

    def _log_audit(self, res: ExecutionResult, decision_hash: str):
        audit_rec = ExecutionAuditRecord(
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            execution_id=res.execution_id,
            authorization_id=res.authorization_id,
            decision_id=res.decision_id,
            action_type=res.action_type,
            amount_minor=res.amount.amount_minor,
            currency=res.amount.currency,
            status=res.status,
            failure_code=res.failure_code,
            decision_hash=decision_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider=res.provider,
            provider_environment=res.provider_environment,
            refund_id=res.refund_id,
            payment_id=res.payment_id,
        )
        self.audit_records.append(audit_rec)
