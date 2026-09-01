"""
TrustLedger Execution Gateway REST API
Phase 7 Bounded Financial Execution Layer
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from decision_gate.models import DecisionResult
from execution_engine.models import ExecutionAuthorization, ExecutionResult, EXECUTION_SIMULATOR_VERSION
from execution_engine.gateway import ExecutionGateway

app = FastAPI(
    title="TrustLedger Execution Gateway REST API",
    description="Bounded Financial Execution Simulator Gateway for TrustLedger Financial AI Firewall",
    version="1.0.0",
)

gateway = ExecutionGateway()


class ExecutePayload(BaseModel):
    authorization_id: str
    decision_result: DecisionResult
    request: Dict[str, Any]
    idempotency_key: Optional[str] = None


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "trustledger-execution-gateway",
        "version": EXECUTION_SIMULATOR_VERSION,
        "mode": gateway.config.simulator_mode,
    }


@app.post("/api/v1/execution/authorize", response_model=ExecutionAuthorization)
def authorize_decision(decision_result: DecisionResult):
    try:
        return gateway.authorize(decision_result)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/execution/execute", response_model=ExecutionResult)
def execute_financial_action(payload: ExecutePayload):
    try:
        return gateway.execute(
            authorization_id=payload.authorization_id,
            decision_result=payload.decision_result,
            request=payload.request,
            idempotency_key=payload.idempotency_key,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/execution/{execution_id}")
def get_execution_record(execution_id: str):
    res = gateway.execution_results.get(execution_id)
    if not res:
        raise HTTPException(status_code=404, detail="Execution record not found")
    return res
