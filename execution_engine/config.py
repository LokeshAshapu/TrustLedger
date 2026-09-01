"""
TrustLedger Execution Engine Configuration Loader
Phase 7 Bounded Financial Execution Layer
"""

import os
from typing import Dict, Any, List
import yaml

DEFAULT_CONFIG_PATH = os.path.join("config", "execution.yaml")


class ExecutionConfig:
    """
    Loads and provides strongly typed access to execution configuration parameters from execution.yaml.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        if not os.path.exists(config_path):
            alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "execution.yaml")
            if os.path.exists(alt_path):
                config_path = alt_path

        with open(config_path, "r", encoding="utf-8") as f:
            self._raw = yaml.safe_load(f)

        self.version: str = self._raw.get("version", "trustledger.execution-simulator.v1")
        self.authorization_ttl_seconds: int = int(self._raw.get("authorization_ttl_seconds", 300))
        self.idempotency_enabled: bool = bool(self._raw.get("idempotency_enabled", True))
        self.strict_hash_validation: bool = bool(self._raw.get("strict_hash_validation", True))
        self.prevent_replay: bool = bool(self._raw.get("prevent_replay", True))
        self.prevent_tampering: bool = bool(self._raw.get("prevent_tampering", True))
        self.supported_action_types: List[str] = self._raw.get("supported_action_types", ["REFUND", "DISCOUNT", "PAYMENT_RECOVERY", "PAYOUT"])
        self.simulator_mode: str = self._raw.get("simulator_mode", "synthetic")
