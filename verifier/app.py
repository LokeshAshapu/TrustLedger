"""
TrustLedger AI Contextual Verification REST API
Phase 5 AI Contextual Verification Layer
"""

from fastapi import FastAPI, HTTPException
from verifier.ai_models import AIVerificationPacket, AIVerificationResult, AI_VERIFIER_VERSION
from verifier.service import AIVerificationService

app = FastAPI(
    title="TrustLedger AI Contextual Verification API",
    description="Contextual AI Reasoning Layer for TrustLedger Financial AI Firewall",
    version="1.0.0",
)

service = AIVerificationService()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "trustledger-ai-verifier",
        "version": AI_VERIFIER_VERSION,
        "provider": service.provider.__class__.__name__,
    }


@app.post("/api/v1/verify/context", response_model=AIVerificationResult)
def verify_context(packet: AIVerificationPacket):
    try:
        return service.verify_context(packet)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
