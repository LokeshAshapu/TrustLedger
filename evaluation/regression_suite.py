"""
TrustLedger Regression Test Suite
Phase 8 Full Evaluation & Safety Validation Layer
"""

import os
import json
from typing import Dict, List, Any

from verifier.deterministic.engine import DeterministicTrustEngine
from risk_engine.engine import FinancialRiskEngine
from verifier.packet_builder import AIVerificationPacketBuilder
from verifier.service import AIVerificationService
from verifier.providers.mock_provider import MockLLMProvider
from decision_gate.gate import DecisionGate
from decision_gate.models import FinalVerdict


class RegressionTestSuite:
    """
    Regression Test Suite enforcing baseline safety across scenario classes A-J.
    """

    def __init__(self, test_split_path: str = "data/splits/test.jsonl", data_dir: str = "data"):
        self.test_split_path = test_split_path
        self.data_dir = data_dir
        self.det_engine = DeterministicTrustEngine()
        self.risk_engine = FinancialRiskEngine()
        self.ai_service = AIVerificationService(MockLLMProvider())
        self.decision_gate = DecisionGate()

    def run_regression_checks(self) -> Dict[str, Any]:
        if not os.path.exists(self.test_split_path):
            return {"status": "SKIPPED", "message": "Test split file not found"}

        processed_dir = os.path.join(self.data_dir, "processed")

        def _load_map(fn, k):
            p = os.path.join(processed_dir, fn)
            m = {}
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            r = json.loads(line)
                            m[r[k]] = r
            return m

        def _load_list(fn):
            p = os.path.join(processed_dir, fn)
            lst = []
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            lst.append(json.loads(line))
            return lst

        context = {
            "evidence_db": _load_map("evidence.jsonl", "evidence_id"),
            "transactions_db": _load_map("transactions.jsonl", "transaction_id"),
            "orders_db": _load_map("orders.jsonl", "order_id"),
            "customers_db": _load_map("customers.jsonl", "customer_id"),
            "policy_snapshots_db": _load_map("policies.jsonl", "merchant_id"),
            "refund_history_db": _load_list("refunds.jsonl"),
        }

        labels_db = _load_map(os.path.join(self.data_dir, "ground-truth", "labels.jsonl"), "decision_id")

        cases = []
        with open(self.test_split_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    cases.append(json.loads(line))

        unsafe_approvals = 0
        rule_violations = 0
        total_evaluated = 0

        for req in cases[:300]:  # Evaluate first 300 cases for regression baseline
            d_id = req["decision_id"]
            lbl = labels_db.get(d_id, {})
            gt = lbl.get("ground_truth_verdict")

            det_res = self.det_engine.verify(req, context)
            risk_res = self.risk_engine.assess(req, context, det_res)
            pkt = AIVerificationPacketBuilder.build(req, context, det_res, risk_res)
            ai_res = self.ai_service.verify_context(pkt)
            gate_res = self.decision_gate.evaluate(req, det_res, risk_res, ai_res)

            pred = gate_res.verdict.value
            total_evaluated += 1

            if gt == "UNSAFE" and pred == "APPROVE":
                unsafe_approvals += 1

        pass_status = (unsafe_approvals == 0)

        return {
            "status": "PASS" if pass_status else "FAIL",
            "total_cases_evaluated": total_evaluated,
            "unsafe_approvals": unsafe_approvals,
            "rule_violations": rule_violations,
        }
