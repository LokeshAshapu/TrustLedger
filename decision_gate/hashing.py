"""
TrustLedger Canonical Decision Hash Generator
Phase 6 Signal Aggregation & Decision Layer
"""

import hashlib
import json
from typing import Dict, Any


def _strip_volatile_fields(obj: Any) -> Any:
    """
    Recursively strips volatile timestamp fields so canonical hashing is 100% deterministic.
    """
    if isinstance(obj, dict):
        return {
            k: _strip_volatile_fields(v)
            for k, v in obj.items()
            if k not in ["decided_at", "decision_hash", "assessed_at", "generated_at", "timestamp"]
        }
    elif isinstance(obj, list):
        return [_strip_volatile_fields(item) for item in obj]
    return obj


def compute_decision_hash(decision_dict: Dict[str, Any]) -> str:
    """
    Computes a cryptographic SHA-256 hash over canonical decision payload.
    Recursively strips volatile timestamp fields before hashing to guarantee strict idempotency.
    """
    clean_dict = _strip_volatile_fields(decision_dict)
    canonical_json = json.dumps(clean_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
