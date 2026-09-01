"""
TrustLedger Real NVIDIA / OpenAI LLM Provider Adapter
Phase 5 AI Contextual Verification Layer
"""

import json
import os
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from verifier.ai_models import (
    AIVerificationPacket,
    AIVerificationResult,
    AIRecommendation,
    AI_VERIFIER_VERSION,
)
from verifier.providers.base import LLMProvider
from verifier.prompt import SYSTEM_PROMPT, render_user_prompt
from verifier.validation import AIValidationEngine


class NVIDIAProvider(LLMProvider):
    """
    Real Provider Adapter supporting NVIDIA API and OpenAI-compatible Chat Completion endpoints.
    Reads credentials from NVIDIA_API_KEY or OPENAI_API_KEY environment variables.
    """

    def __init__(self, model_id: str = None, timeout_seconds: float = 10.0):
        self.model_id = model_id or os.getenv("AI_MODEL", "meta/llama-3.1-70b-instruct")
        self.timeout_seconds = float(os.getenv("AI_TIMEOUT_SECONDS", str(timeout_seconds)))
        self.api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("AI_BASE_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
        self.validator = AIValidationEngine()

    def verify(self, packet: AIVerificationPacket) -> AIVerificationResult:
        if not self.api_key:
            raise ValueError("No API key configured. Set NVIDIA_API_KEY or OPENAI_API_KEY in environment.")

        user_prompt = render_user_prompt(packet.model_dump())

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"},
        }

        data_bytes = json.dumps(body).encode("utf-8")

        # Execute call with bounded retry (1 retry)
        last_error = None
        for attempt in range(2):
            try:
                req = urllib.request.Request(self.base_url, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    res_bytes = response.read()
                    res_json = json.loads(res_bytes.decode("utf-8"))

                content_str = res_json["choices"][0]["message"]["content"]
                raw_parsed = json.loads(content_str)

                # Validate schema and citations
                return self.validator.validate(raw_parsed, packet)

            except Exception as e:
                last_error = e
                time.sleep(0.5)

        raise RuntimeError(f"NVIDIA/OpenAI provider failed after 2 attempts. Error: {last_error}")
