"""
TrustLedger Synthetic AI Agent Client & Non-Bypass Demo Architecture
Phase 7 Bounded Financial Execution Layer
"""

from typing import Dict, Any, Tuple, Optional
from decision_gate.models import DecisionResult, FinalVerdict
from execution_engine.models import ExecutionResult, FailureCode
from execution_engine.gateway import ExecutionGateway
from verifier.packet_builder import AIVerificationPacketBuilder


class AIAgentClient:
    """
    Synthetic AI Agent Proposal Client.
    Demonstrates the strict Non-Bypass Architecture: the AI Agent has ZERO direct access
    to the financial simulator and must submit all proposals through TrustLedger's decision pipeline.
    """

    def __init__(self, agent_id: str = "agent_support_bot_01"):
        self.agent_id = agent_id

    def propose_and_execute(
        self,
        request: Dict[str, Any],
        context: Dict[str, Any],
        det_engine: Any,
        risk_engine: Any,
        ai_service: Any,
        decision_gate: Any,
        execution_gateway: ExecutionGateway,
    ) -> Tuple[DecisionResult, Optional[Any], Optional[ExecutionResult]]:

        # 1. Submit proposal to Phase 3 Deterministic Engine
        det_res = det_engine.verify(request, context)

        # 2. Submit to Phase 4 Financial Risk Engine
        risk_res = risk_engine.assess(request, context, det_res)

        # 3. Submit to Phase 5 AI Contextual Verifier
        packet = AIVerificationPacketBuilder.build(request, context, det_res, risk_res)
        ai_res = ai_service.verify_context(packet)

        # 4. Submit to Phase 6 Decision Gate
        gate_res = decision_gate.evaluate(request, det_res, risk_res, ai_res)

        # Non-Bypass Enforcer: Only APPROVE decisions may proceed to Authorization and Execution!
        if gate_res.verdict != FinalVerdict.APPROVE:
            # For REVIEW and BLOCK decisions: Authorization is NOT created and execution is NOT attempted!
            return gate_res, None, None

        # 5. Issue Execution Authorization Token for APPROVE verdict
        auth = execution_gateway.authorize(gate_res)

        # 6. Execute Synthetic Financial Action over Gateway
        exec_res = execution_gateway.execute(
            authorization_id=auth.authorization_id,
            decision_result=gate_res,
            request=request,
            idempotency_key=f"idemp_{auth.authorization_id}",
        )

        return gate_res, auth, exec_res

    def attempt_direct_execution_bypass(
        self,
        execution_gateway: ExecutionGateway,
        request: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Attempts direct execution bypass without going through TrustLedger.
        Demonstrates that direct execution fails immediately with AUTHORIZATION_NOT_FOUND.
        """
        fake_auth_id = "auth_bypassed_fake_id"

        return execution_gateway.execute(
            authorization_id=fake_auth_id,
            decision_result=None,
            request=request,
        )
