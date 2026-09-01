"""
TrustLedger Verification Packet Builder
Phase 5 AI Contextual Verification Layer
"""

from typing import Dict, Any, List
from verifier.ai_models import AIVerificationPacket
from verifier.deterministic.models import DeterministicVerificationResult
from risk_engine.models import RiskAssessment


class AIVerificationPacketBuilder:
    """
    Constructs a minimal, rank-ordered AIVerificationPacket containing only
    legitimate observable data, evidence artifacts, deterministic findings,
    and risk assessment details. Enforces strict ground-truth isolation.
    """

    @staticmethod
    def build(
        request: Dict[str, Any],
        context: Dict[str, Any],
        det_result: DeterministicVerificationResult,
        risk_assessment: RiskAssessment,
    ) -> AIVerificationPacket:
        evidence_db = context.get("evidence_db", {})
        transactions_db = context.get("transactions_db", {})
        orders_db = context.get("orders_db", {})
        customers_db = context.get("customers_db", {})
        policies_db = context.get("policy_snapshots_db", {})
        refund_history_db = context.get("refund_history_db", [])

        # Clean Request (Ensure ground-truth fields are absent)
        clean_req = {k: v for k, v in request.items() if not k.startswith("ground_truth") and k not in ["scenario_class", "expected_verdict", "is_safe"]}

        # Collect Relevant Evidence Artifacts
        ev_refs = request.get("evidence_references", [])
        relevant_evidence = []
        for ev_id in ev_refs:
            if ev_id in evidence_db:
                rec = {k: v for k, v in evidence_db[ev_id].items() if not k.startswith("ground_truth")}
                relevant_evidence.append(rec)

        # Collect Related Financial Records
        txn_id = request.get("transaction_id")
        order_id = request.get("order_id")
        cust_id = request.get("customer_id")
        merch_id = request.get("merchant_id")

        related_records = {
            "transaction": transactions_db.get(txn_id) if txn_id else None,
            "order": orders_db.get(order_id) if order_id else None,
            "customer": customers_db.get(cust_id) if cust_id else None,
            "historical_refunds": [
                r for r in refund_history_db
                if r.get("transaction_id") == txn_id or r.get("customer_id") == cust_id
            ][:5],
        }

        # Policy Snapshot
        policy_snap = policies_db.get(merch_id, {})

        return AIVerificationPacket(
            decision=clean_req,
            relevant_evidence=relevant_evidence,
            related_records={k: v for k, v in related_records.items() if v is not None},
            policy_snapshot=policy_snap,
            deterministic_result=det_result.model_dump(),
            risk_assessment=risk_assessment.model_dump(),
        )
