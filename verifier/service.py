"""
TrustLedger Master AI Contextual Verification Service
Phase 5 AI Contextual Verification Layer
"""

import os
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    AI_VERIFIER_VERSION,
)
from verifier.providers.base import LLMProvider
from verifier.providers.mock_provider import MockLLMProvider
from verifier.providers.nvidia_provider import NVIDIAProvider


class AIVerificationService:
    """
    Master AI Contextual Verification Service.
    Selects the configured provider (NVIDIA, OpenAI, or Mock), executes verification,
    and guarantees fail-safe fallback (AI_UNAVAILABLE) if the provider fails.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        if provider:
            self.provider = provider
        else:
            provider_type = os.getenv("AI_PROVIDER", "mock").lower()
            if provider_type in ["nvidia", "openai"]:
                try:
                    self.provider = NVIDIAProvider()
                except Exception:
                    self.provider = MockLLMProvider()
            else:
                self.provider = MockLLMProvider()

    def verify_context(self, packet: AIVerificationPacket) -> AIVerificationResult:
        d_id = packet.decision.get("decision_id", "unknown")

        try:
            return self.provider.verify(packet)
        except Exception as e:
            # Fail-Safe Fallback: Return structured AI_UNAVAILABLE result
            return AIVerificationResult(
                decision_id=d_id,
                recommendation=AIRecommendation.UNCERTAIN,
                confidence=0.0,
                contextual_assessment=f"AI contextual verification service unavailable: {str(e)}. Deferring decision to safety gate.",
                supporting_evidence=[],
                contradictory_evidence=[],
                missing_context=["AI verification service timeout or provider failure."],
                reasoning_factors=[],
                deterministic_conflicts=[],
                model_id=getattr(self.provider, "model_id", "ai_unavailable"),
                verifier_version=AI_VERIFIER_VERSION,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
