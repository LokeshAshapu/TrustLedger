"""
TrustLedger Financial Risk Engine Configuration Loader
Phase 4 Deterministic Financial Risk Layer
"""

import os
from typing import Dict, Any
import yaml

DEFAULT_CONFIG_PATH = os.path.join("config", "risk.yaml")


class RiskConfig:
    """
    Loads and provides strongly typed access to risk configuration parameters from risk.yaml.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        if not os.path.exists(config_path):
            # Fallback to root relative path if needed
            alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "risk.yaml")
            if os.path.exists(alt_path):
                config_path = alt_path

        with open(config_path, "r", encoding="utf-8") as f:
            self._raw = yaml.safe_load(f)

        self.version: str = self._raw.get("version", "trustledger.risk.v1")

        # Exposure Bands (in minor units / paise)
        bands = self._raw.get("exposure_bands", {})
        self.low_max_minor: int = bands.get("low_max_minor", 1000000)
        self.medium_max_minor: int = bands.get("medium_max_minor", 5000000)
        self.high_max_minor: int = bands.get("high_max_minor", 20000000)
        self.critical_min_minor: int = bands.get("critical_min_minor", 20000001)

        # Action Weights & Irreversibility
        self.action_weights: Dict[str, float] = self._raw.get("action_weights", {
            "PAYOUT": 1.0, "REFUND": 0.8, "PAYMENT_RECOVERY": 0.6, "DISCOUNT": 0.4
        })
        self.action_irreversibility: Dict[str, float] = self._raw.get("action_irreversibility", {
            "PAYOUT": 0.90, "REFUND": 0.50, "PAYMENT_RECOVERY": 0.30, "DISCOUNT": 0.20
        })

        # Finding Severity Weights
        self.finding_weights: Dict[str, float] = self._raw.get("finding_weights", {
            "HARD": 0.30, "WARNING": 0.10, "INFO": 0.00
        })

        # Risk Level Thresholds
        thresholds = self._raw.get("risk_level_thresholds", {})
        self.low_upper: float = thresholds.get("low_upper", 0.25)
        self.medium_upper: float = thresholds.get("medium_upper", 0.50)
        self.high_upper: float = thresholds.get("high_upper", 0.75)
