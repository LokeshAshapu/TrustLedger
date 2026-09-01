"""
TrustLedger Abstract LLM Provider Interface
Phase 5 AI Contextual Verification Layer
"""

from abc import ABC, abstractmethod
from verifier.ai_models import AIVerificationPacket, AIVerificationResult


class LLMProvider(ABC):
    """
    Abstract LLM Provider interface for TrustLedger AI Verification Engine.
    All real and mock provider adapters must inherit from this class.
    """

    @abstractmethod
    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        """
        Executes contextual AI verification over the input packet.
        Must return a valid AIVerificationResult.
        """
        pass
