"""
TrustLedger Master End-to-End Decision Orchestrator
Phase 10A End-to-End Backend Orchestration
Orchestration Version: trustledger.orchestrator.v1
"""

import copy
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from verifier.deterministic.engine import DeterministicTrustEngine
from verifier.deterministic.schema_validator import SchemaValidator
from verifier.deterministic.models import CheckStatus
from risk_engine.engine import FinancialRiskEngine
from verifier.packet_builder import AIVerificationPacketBuilder
from verifier.service import AIVerificationService
from verifier.providers.mock_provider import MockLLMProvider
from decision_gate.gate import DecisionGate
from decision_gate.models import DecisionResult, FinalVerdict
from execution_engine.gateway import ExecutionGateway
from execution_engine.models import ExecutionAuthorization, ExecutionResult
from backend.repository import SyntheticDataRepository

logger = logging.getLogger("trustledger.orchestrator")


class TrustLedgerDecisionService:
    """
    Master Backend Orchestrator Service.
    Coordinates contract validation, data resolution, deterministic verifier,
    financial risk engine, AI verifier, Decision Gate, and execution boundary.
    """

    def __init__(
        self,
        data_repository: Optional[SyntheticDataRepository] = None,
        deterministic_engine: Optional[DeterministicTrustEngine] = None,
        risk_engine: Optional[FinancialRiskEngine] = None,
        ai_service: Optional[AIVerificationService] = None,
        decision_gate: Optional[DecisionGate] = None,
        execution_gateway: Optional[ExecutionGateway] = None,
    ):
        self.repository = data_repository or SyntheticDataRepository()
        self.schema_validator = SchemaValidator()
        self.deterministic_engine = deterministic_engine or DeterministicTrustEngine()
        self.risk_engine = risk_engine or FinancialRiskEngine()
        self.ai_service = ai_service or AIVerificationService(MockLLMProvider())
        self.decision_gate = decision_gate or DecisionGate()
        self.execution_gateway = execution_gateway or ExecutionGateway()

        self.decisions_db: Dict[str, DecisionResult] = {}
        self.requests_db: Dict[str, Dict[str, Any]] = {}

    def verify_decision(
        self, request: Dict[str, Any]
    ) -> Tuple[DecisionResult, Optional[ExecutionAuthorization]]:
        """
        Executes end-to-end TrustLedger decision pipeline:
        Request -> Contract -> Evidence -> Deterministic -> Policy -> Consistency -> Risk -> AI -> Decision Gate -> Authorization Boundary.
        """
        start_time = datetime.now(timezone.utc)
        d_id = request.get("decision_id", "unknown_decision")

        logger.info(
            f"[ORCHESTRATION START] decision_id='{d_id}' "
            f"action='{request.get('action_type')}' "
            f"amount={request.get('amount')} "
            f"merchant='{request.get('merchant_id')}'"
        )

        # 1. Canonical Contract Schema Validation
        schema_res = self.schema_validator.validate(request)
        logger.info(f"[SCHEMA] decision_id='{d_id}' status={schema_res.status.value} findings={len(schema_res.findings)}")
        if schema_res.status != CheckStatus.PASS:
            for f in schema_res.findings:
                logger.warning(f"  [SCHEMA FINDING] {f.code}: {f.message}")

        # 2. Data Context Resolution from Synthetic World Data Repository
        context = self.repository.get_context_for_request(request)

        # 2b. Razorpay Test-Mode Payment Context Integration
        pid = request.get("payment_id") or request.get("transaction_id")
        if pid and str(pid).startswith("pay_"):
            try:
                rzp_client = self.execution_gateway.razorpay_client
                if rzp_client.key_id and rzp_client.key_secret and rzp_client.environment == "test":
                    raw_pay = rzp_client.fetch_payment(str(pid).strip())
                    if raw_pay and "id" in raw_pay:
                        amount_minor = raw_pay.get("amount", 0)
                        is_captured = bool(raw_pay.get("captured", False)) or raw_pay.get("status") == "captured"
                        created_ts = raw_pay.get("created_at")
                        created_iso = str(created_ts or "2026-08-30T10:00:00Z")

                        rzp_txn_rec = {
                            "transaction_id": raw_pay["id"],
                            "order_id": request.get("order_id") or raw_pay.get("order_id") or "ord_rzp",
                            "merchant_id": request.get("merchant_id", "merch_001"),
                            "customer_id": request.get("customer_id", "cust_001"),
                            "amount": {"amount_minor": amount_minor, "currency": raw_pay.get("currency", "INR")},
                            "payment_method": str(raw_pay.get("method", "CARD")).upper(),
                            "status": "CAPTURED" if is_captured else str(raw_pay.get("status", "UNCAPTURED")).upper(),
                            "created_at": created_iso,
                            "source": "RAZORPAY_TEST_MODE",
                        }
                        context["transactions_db"][raw_pay["id"]] = rzp_txn_rec
                        if pid != raw_pay["id"]:
                            context["transactions_db"][pid] = rzp_txn_rec
            except Exception as e:
                logger.info(f"Razorpay live payment lookup for '{pid}' skipped: {e}")

        req_cust_id = request.get("customer_id")
        if pid and req_cust_id and pid in context["transactions_db"]:
            context["transactions_db"][pid]["customer_id"] = req_cust_id

        # 3. Deterministic Verification Engine (Schema, Evidence, Policy, Consistency)
        det_result = self.deterministic_engine.verify(request, context)

        logger.info(
            f"[DETERMINISTIC] decision_id='{d_id}' "
            f"schema={det_result.schema_result.status.value} "
            f"evidence={det_result.evidence_result.status.value} "
            f"policy={det_result.policy_result.status.value} "
            f"consistency={det_result.consistency_result.status.value} "
            f"hard_failures={len(det_result.hard_failures)} "
            f"warnings={len(det_result.warnings)}"
        )
        for hf in det_result.hard_failures:
            logger.warning(f"  [HARD FAILURE] {hf.code}: {hf.message}")
        for w in det_result.warnings:
            logger.info(f"  [WARNING] {w.code}: {w.message}")

        # 4. Financial Risk Engine
        risk_assessment = self.risk_engine.assess(request, context, det_result)
        logger.info(
            f"[RISK] decision_id='{d_id}' "
            f"level={risk_assessment.risk_level.value} "
            f"score={risk_assessment.risk_score:.4f} "
            f"gross_exposure={risk_assessment.exposure.gross_exposure.amount_minor}"
        )

        # 5. AI Verification Packet Construction & Contextual AI Verification
        ai_packet = AIVerificationPacketBuilder.build(
            request, context, det_result, risk_assessment
        )
        ai_result = self.ai_service.verify_context(ai_packet)
        logger.info(
            f"[AI CONTEXT] decision_id='{d_id}' "
            f"recommendation={ai_result.recommendation.value} "
            f"confidence={ai_result.confidence:.2f} "
            f"model={ai_result.model_id}"
        )

        # 6. Authoritative Decision Gate Signal Aggregation
        decision_result = self.decision_gate.evaluate(
            request, det_result, risk_assessment, ai_result
        )

        # Store Decision & Request in backend state for server-side lookup
        self.decisions_db[d_id] = decision_result
        self.requests_db[d_id] = request

        # 7. Execution Authorization Boundary Protection
        authorization: Optional[ExecutionAuthorization] = None
        if decision_result.verdict == FinalVerdict.APPROVE:
            try:
                authorization = self.execution_gateway.authorize(decision_result)
                logger.info(
                    f"[AUTH] ISSUED auth_id='{authorization.authorization_id}' "
                    f"for decision_id='{d_id}'"
                )
            except Exception as e:
                logger.error(f"[AUTH] Authorization issuance failed for decision_id='{d_id}': {str(e)}")
                authorization = None
        else:
            logger.info(
                f"[AUTH] DENIED verdict='{decision_result.verdict.value}' decision_id='{d_id}'"
            )

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.info(
            f"[ORCHESTRATION END] decision_id='{d_id}' "
            f"verdict='{decision_result.verdict.value}' "
            f"rule='{decision_result.decision_rule}' "
            f"primary_reason='{decision_result.primary_reason.code}' "
            f"duration_ms={duration_ms:.2f}ms"
        )

        return decision_result, authorization

    def execute_decision(
        self, decision_id: str, authorization_id: str, payment_id: str, idempotency_key: Optional[str] = None
    ) -> ExecutionResult:
        """
        Executes an authorized refund via RazorpayTestClient.
        Loads authoritative DecisionResult from backend state. Verdict CANNOT be supplied by caller.
        """
        decision_result = self.decisions_db.get(decision_id)
        original_request = self.requests_db.get(decision_id, {})

        # Prepare request payload with payment_id
        exec_request = copy.deepcopy(original_request)
        exec_request["payment_id"] = payment_id
        if idempotency_key:
            exec_request["idempotency_key"] = idempotency_key

        return self.execution_gateway.execute(
            authorization_id=authorization_id,
            decision_result=decision_result,
            request=exec_request,
            idempotency_key=idempotency_key,
            use_razorpay=True,
        )
