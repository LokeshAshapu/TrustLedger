"""
TrustLedger Server-Side Razorpay Test-Mode Refund Models
Phase 11B.1 Razorpay Test-Mode Refund Client
"""

import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class RefundRequest(BaseModel):
    """
    Strongly typed Pydantic model for Razorpay refund execution request.
    Strictly validates payment_id, amount_minor (integer paise), currency,
    idempotency_key, receipt, and notes.
    """
    payment_id: str = Field(min_length=1, description="Razorpay payment ID (e.g. pay_L123456789)")
    amount_minor: int = Field(gt=0, description="Refund amount in minor currency units (paise for INR)")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="3-letter uppercase currency code")
    idempotency_key: str = Field(min_length=10, description="Idempotency key for X-Refund-Idempotency header")
    receipt: Optional[str] = Field(default=None, max_length=40, description="Optional merchant receipt identifier")
    notes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional key-value notes (max 15 pairs)")

    @field_validator("payment_id")
    @classmethod
    def validate_payment_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("payment_id must be a non-empty string.")
        return v.strip()

    @field_validator("amount_minor", mode="before")
    @classmethod
    def validate_amount_minor(cls, v: Any) -> int:
        if isinstance(v, float):
            raise ValueError("amount_minor must be a strict integer, float values are rejected.")
        if isinstance(v, bool):
            raise ValueError("amount_minor must be an integer, bool values are rejected.")
        try:
            val = int(v)
        except (ValueError, TypeError):
            raise ValueError("amount_minor must be a valid positive integer.")
        if val <= 0:
            raise ValueError("amount_minor must be a positive integer greater than zero.")
        return val

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not v or len(v) != 3 or not v.isupper() or not v.isalpha():
            raise ValueError("currency must be a 3-character uppercase ISO currency code (e.g. 'INR').")
        return v

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("idempotency_key must be at least 10 characters long.")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("idempotency_key must contain only alphanumeric characters, hyphens, or underscores.")
        return v

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is not None and len(v) > 15:
            raise ValueError("notes dictionary must not exceed 15 key-value pairs.")
        return v


class RefundResponse(BaseModel):
    """
    Normalized response object returned by RazorpayTestClient.
    Conforms strictly to Razorpay's documented refund schema without exposing API keys.
    """
    refund_id: str = Field(min_length=1)
    payment_id: str = Field(min_length=1)
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    status: str = Field(min_length=1)
    receipt: Optional[str] = None
    notes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: Optional[Any] = None
    raw_response_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
