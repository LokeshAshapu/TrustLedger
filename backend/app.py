"""
TrustLedger Master REST API Server
Phase 11B.2, 11B.3, 11C.2, 11C.7 — Amount Normalization & Explainable Decision API
API Version: trustledger.api.v1
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from decision_gate.models import DecisionResult
from execution_engine.models import ExecutionAuthorization, ExecutionResult
from execution.errors import (
    RazorpayClientError,
    RazorpayConfigurationError,
    RazorpayAuthenticationError,
    RazorpayNotFoundError,
    RazorpayValidationError,
)
from backend.orchestrator import TrustLedgerDecisionService
from backend.repository import SyntheticDataRepository
from backend.normalizer import normalize_request, RequestNormalizationError

logger = logging.getLogger("trustledger.api")

app = FastAPI(
    title="TrustLedger Financial AI Firewall REST API",
    description="Authoritative End-to-End Decision & Verification API for Financial AI Agents",
    version="1.0.0",
)

# Enable CORS with configurable origin restrictions for production hardening
cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Orchestration Service Singleton
repository = SyntheticDataRepository()
decision_service = TrustLedgerDecisionService(data_repository=repository)


class DecisionResponse(BaseModel):
    decision_result: DecisionResult
    authorization: Optional[ExecutionAuthorization] = None


class ExecuteRefundApiRequest(BaseModel):
    authorization_id: str = Field(min_length=1, description="Valid ExecutionAuthorization ID issued by Decision Gate")
    payment_id: str = Field(min_length=1, description="Razorpay payment ID to execute refund against")
    idempotency_key: Optional[str] = Field(default=None, description="Optional idempotency key for safe retry")


class CreateOrderRequest(BaseModel):
    amount: float = Field(..., description="Amount in INR (e.g., 1500.0) or minor units")
    currency: str = Field("INR", description="3-letter ISO currency code")
    customer_name: Optional[str] = Field("Demo Customer", description="Customer full name")
    customer_email: Optional[str] = Field("demo@example.com", description="Customer email address")
    notes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary metadata notes")


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str = Field(..., description="Captured Razorpay Payment ID (e.g. pay_...)")
    razorpay_order_id: str = Field(..., description="Razorpay Order ID (e.g. order_...)")
    razorpay_signature: str = Field(..., description="HMAC-SHA256 signature returned by Razorpay Checkout")
    amount: Optional[float] = Field(None, description="Payment amount in INR")
    currency: Optional[str] = Field("INR", description="Currency code")


@app.get("/health")
def health_check():
    """
    Health check endpoint exposing system & component status.
    Distinguishes configured AI provider and API key presence.
    """
    provider_type = os.getenv("AI_PROVIDER", "mock").lower()
    has_api_key = bool(os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY"))

    ai_provider_status = {
        "configured_provider": provider_type,
        "model_id": os.getenv("AI_MODEL", "meta/llama-3.1-70b-instruct"),
        "key_status": "configured" if has_api_key else ("mock_mode" if provider_type == "mock" else "missing_key"),
        "status": "available" if (provider_type == "mock" or has_api_key) else "degraded_fallback_to_review",
    }

    return {
        "status": "healthy",
        "service": "trustledger-orchestration-api",
        "contract_version": "trustledger.contract.v1",
        "components": {
            "deterministic_engine": "available",
            "risk_engine": "available",
            "ai_verifier": ai_provider_status,
            "decision_gate": "available",
            "execution_gateway": "available",
            "razorpay_client": decision_service.execution_gateway.razorpay_client.health_check(),
            "synthetic_world_repository": f"available ({len(repository.transactions_db)} transactions loaded)",
        },
    }


@app.get("/health/razorpay")
def razorpay_health_check():
    """
    GET /health/razorpay
    Explicit Razorpay Test Mode health/preflight check.
    Returns safe metadata. Never exposes API key secrets or Authorization headers.
    """
    rzp_client = decision_service.execution_gateway.razorpay_client
    check = rzp_client.health_check()
    return {
        "configured": check.get("configured", False),
        "environment": check.get("environment", "test"),
        "base_url": check.get("base_url", "https://api.razorpay.com"),
        "credentials_present": check.get("key_status") == "configured",
        "details": check,
    }


@app.post("/api/v1/razorpay/test/orders")
def create_razorpay_test_order(req: CreateOrderRequest):
    """
    POST /api/v1/razorpay/test/orders
    Creates a Razorpay Test Mode Order for initializing Web Checkout.
    Never exposes key_secret to client.
    """
    rzp_client = decision_service.execution_gateway.razorpay_client

    if req.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_AMOUNT", "message": "Order amount must be greater than zero."},
        )

    amount_minor = int(round(req.amount * 100))
    amount_rupees = round(amount_minor / 100.0, 2)

    try:
        order_data = rzp_client.create_order(
            amount_minor=amount_minor,
            currency=req.currency,
            notes=req.notes or {"customer_name": req.customer_name, "customer_email": req.customer_email},
        )
        return {
            "order_id": order_data.get("id"),
            "amount_minor": order_data.get("amount", amount_minor),
            "amount_rupees": amount_rupees,
            "currency": order_data.get("currency", "INR"),
            "key_id": rzp_client.key_id or "rzp_test_TWo67wxNkq6aZb",
            "environment": rzp_client.environment,
            "source": order_data.get("source", "RAZORPAY_TEST_MODE"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ORDER_CREATION_FAILED: {str(e)}",
        )


@app.post("/api/v1/razorpay/test/payment/verify")
def verify_razorpay_test_payment(req: VerifyPaymentRequest):
    """
    POST /api/v1/razorpay/test/payment/verify
    Verifies Razorpay payment HMAC-SHA256 signature server-side.
    Fetches actual captured payment details from Razorpay Test Mode API.
    Registers captured transaction into repository context for refund verification.
    """
    rzp_client = decision_service.execution_gateway.razorpay_client

    is_valid = rzp_client.verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_PAYMENT_SIGNATURE",
                "message": "Razorpay payment signature verification failed. Possible payload tampering.",
            },
        )

    pid = req.razorpay_payment_id.strip()
    try:
        raw_pay = rzp_client.fetch_payment(pid)
        amount_minor = raw_pay.get("amount", int(req.amount * 100 if req.amount else 150000))
        amount_rupees = round(amount_minor / 100.0, 2)
        payment_method = str(raw_pay.get("method", "CARD")).upper()
        pay_status = str(raw_pay.get("status", "CAPTURED")).upper()
        source = "RAZORPAY_TEST_MODE"
    except Exception:
        amount_rupees = req.amount or 1500.0
        amount_minor = int(round(amount_rupees * 100))
        payment_method = "CARD"
        pay_status = "CAPTURED"
        source = "VERIFIED_TEST_PAYMENT"

    repository.transactions_db[pid] = {
        "transaction_id": pid,
        "order_id": req.razorpay_order_id,
        "amount": {"amount_minor": amount_minor, "currency": req.currency or "INR"},
        "status": pay_status,
        "payment_method": payment_method,
        "refunded_amount": {"amount_minor": 0, "currency": req.currency or "INR"},
        "customer_id": "cust_100",
        "merchant_id": "merch_001",
        "created_at": "2026-08-30T10:00:00Z",
    }

    return {
        "verified": True,
        "payment_id": pid,
        "order_id": req.razorpay_order_id,
        "amount_rupees": amount_rupees,
        "amount_minor": amount_minor,
        "currency": req.currency or "INR",
        "status": pay_status,
        "method": payment_method,
        "source": source,
    }


@app.get("/api/v1/payments/{payment_id}")
def get_razorpay_payment(payment_id: str):
    """
    GET /api/v1/payments/{payment_id}
    Non-mutating read-only payment inspection from Razorpay Test Mode.
    Returns normalized safe payment metadata. Never exposes sensitive credentials.
    """
    pid = (payment_id or "").strip()
    if not pid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_PAYMENT_ID", "message": "payment_id parameter is required."},
        )

    rzp_client = decision_service.execution_gateway.razorpay_client
    local_txn = repository.transactions_db.get(pid)

    try:
        raw_pay = rzp_client.fetch_payment(pid)
        amount_minor = raw_pay.get("amount", 0)
        return {
            "payment_id": raw_pay.get("id", pid),
            "amount_minor": amount_minor,
            "amount_rupees": round(amount_minor / 100.0, 2),
            "currency": raw_pay.get("currency", "INR"),
            "status": str(raw_pay.get("status", "unknown")).upper(),
            "captured": bool(raw_pay.get("captured", False)) or raw_pay.get("status") == "captured",
            "method": str(raw_pay.get("method", "CARD")).upper(),
            "created_at": raw_pay.get("created_at"),
            "email": raw_pay.get("email"),
            "contact": raw_pay.get("contact"),
            "source": "RAZORPAY_TEST_MODE",
        }
    except (RazorpayNotFoundError, RazorpayClientError, RazorpayValidationError):
        if local_txn:
            amount_minor = local_txn.get("amount", {}).get("amount_minor", 0)
            return {
                "payment_id": local_txn.get("transaction_id"),
                "amount_minor": amount_minor,
                "amount_rupees": round(amount_minor / 100.0, 2),
                "currency": local_txn.get("amount", {}).get("currency", "INR"),
                "status": str(local_txn.get("status", "CAPTURED")).upper(),
                "captured": local_txn.get("status") == "CAPTURED",
                "method": str(local_txn.get("payment_method", "CARD")).upper(),
                "created_at": local_txn.get("created_at"),
                "source": "HELD-OUT BENCHMARK",
            }
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "PAYMENT_NOT_FOUND",
                "message": f"Payment ID '{pid}' was not found on Razorpay Test API or local benchmark database.",
            },
        )
    except RazorpayAuthenticationError as ae:
        if local_txn:
            amount_minor = local_txn.get("amount", {}).get("amount_minor", 0)
            return {
                "payment_id": local_txn.get("transaction_id"),
                "amount_minor": amount_minor,
                "amount_rupees": round(amount_minor / 100.0, 2),
                "currency": local_txn.get("amount", {}).get("currency", "INR"),
                "status": str(local_txn.get("status", "CAPTURED")).upper(),
                "captured": local_txn.get("status") == "CAPTURED",
                "method": str(local_txn.get("payment_method", "CARD")).upper(),
                "created_at": local_txn.get("created_at"),
                "source": "HELD-OUT BENCHMARK",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "RAZORPAY_AUTH_ERROR", "message": str(ae)},
        )
    except RazorpayConfigurationError as ce:
        if local_txn:
            amount_minor = local_txn.get("amount", {}).get("amount_minor", 0)
            return {
                "payment_id": local_txn.get("transaction_id"),
                "amount_minor": amount_minor,
                "amount_rupees": round(amount_minor / 100.0, 2),
                "currency": local_txn.get("amount", {}).get("currency", "INR"),
                "status": str(local_txn.get("status", "CAPTURED")).upper(),
                "captured": local_txn.get("status") == "CAPTURED",
                "method": str(local_txn.get("payment_method", "CARD")).upper(),
                "created_at": local_txn.get("created_at"),
                "source": "HELD-OUT BENCHMARK",
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "RAZORPAY_CONFIG_ERROR", "message": str(ce)},
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "RAZORPAY_FETCH_ERROR", "message": str(ex)},
        )


@app.post("/api/v1/decisions/verify", response_model=DecisionResponse)
def verify_decision(request: Dict[str, Any]):
    """
    POST /api/v1/decisions/verify

    Ingests a DecisionRequest payload and returns an authoritative DecisionResult.

    Accepts two formats for 'amount':
    - Simple integer: "amount": 1500  (treated as INR rupees → 150000 paise internally)
    - Structured Money: "amount": {"amount_minor": 150000, "currency": "INR"}

    All other required fields (agent_id, merchant_id, reason, evidence_references, requested_at)
    are optional at the API boundary — safe defaults are applied by the normalizer.
    The canonical Decision Engine always runs in full.
    """
    if not isinstance(request, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_PAYLOAD",
                "message": "Request body must be a valid JSON object.",
            },
        )

    # --- PHASE 1: Normalize public API request → canonical internal format (ONCE, at the boundary) ---
    try:
        canonical_request = normalize_request(request)
        logger.info(
            f"Normalized request decision_id='{canonical_request.get('decision_id')}' "
            f"amount={canonical_request.get('amount')} action={canonical_request.get('action_type')}"
        )
    except RequestNormalizationError as rne:
        logger.warning(f"Request normalization failed: {rne}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "field": rne.field,
                "message": rne.message,
            },
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": str(ve),
            },
        )

    # --- PHASE 2: Run full TrustLedger orchestration pipeline ---
    try:
        decision_result, authorization = decision_service.verify_decision(canonical_request)
        logger.info(
            f"Decision completed decision_id='{decision_result.decision_id}' "
            f"verdict={decision_result.verdict.value} rule={decision_result.decision_rule}"
        )
        return DecisionResponse(
            decision_result=decision_result,
            authorization=authorization,
        )
    except ValueError as ve:
        logger.warning(f"Pipeline ValueError for request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BAD_REQUEST",
                "message": str(ve),
            },
        )
    except Exception as e:
        logger.error(f"Orchestration failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ORCHESTRATION_FAILURE",
                "message": str(e),
            },
        )


@app.post("/api/v1/decisions/{decision_id}/execute", response_model=ExecutionResult)
def execute_refund(decision_id: str, req: ExecuteRefundApiRequest):
    """
    POST /api/v1/decisions/{decision_id}/execute
    Executes an authorized refund via RazorpayTestClient.
    Authoritative DecisionResult is retrieved strictly from server-side state.
    Frontend CANNOT pass a verdict to force execution.
    """
    if not decision_id or not decision_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_DECISION_ID: Decision ID path parameter is required.",
        )

    try:
        exec_result = decision_service.execute_decision(
            decision_id=decision_id,
            authorization_id=req.authorization_id,
            payment_id=req.payment_id,
            idempotency_key=req.idempotency_key,
        )
        return exec_result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"EXECUTION_DENIED: {str(ve)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"EXECUTION_FAILURE: {str(e)}",
        )


# --- Static Frontend Production Serving & SPA Catch-All Routing ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

if os.path.exists(frontend_dist_path):
    index_html_path = os.path.join(frontend_dist_path, "index.html")

    # Serve static assets under /assets
    assets_path = os.path.join(frontend_dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="static_assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Allow API routes to be handled by FastAPI
        if full_path.startswith("api/") or full_path.startswith("health"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API endpoint not found")

        # Check if specific static file exists in dist (e.g. favicon.svg)
        target_file = os.path.join(frontend_dist_path, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)

        # Return SPA index.html for all client-side React routes
        return FileResponse(index_html_path)
