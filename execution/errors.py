"""
TrustLedger Razorpay Test-Mode Client Exceptions
Phase 11B.1 Razorpay Test-Mode Refund Client
"""

import re
from typing import Optional, Dict, Any


def sanitize_secret_text(text: str) -> str:
    """
    Sanitizes string representations to guarantee secrets, API keys, or Basic Auth tokens
    never leak in exception messages, string formatting, or logs.
    """
    if not text:
        return ""
    # Strip Basic Auth headers, key IDs, or key secret patterns
    sanitized = re.sub(r"Basic\s+[A-Za-z0-9+/=]+", "Basic [REDACTED]", text, flags=re.IGNORECASE)
    sanitized = re.sub(r"rzp_test_[A-Za-z0-9]+", "rzp_test_[REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"rzp_live_[A-Za-z0-9]+", "rzp_live_[REDACTED]", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"secret_[A-Za-z0-9_-]+", "secret_[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


class RazorpayClientError(Exception):
    """
    Base exception class for all Razorpay client errors.
    Automatically redacts API keys and secrets from string representations.
    """
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        raw_details: Optional[Dict[str, Any]] = None,
    ):
        self.message = sanitize_secret_text(message)
        self.status_code = status_code
        self.error_code = error_code or "RAZORPAY_CLIENT_ERROR"
        self.raw_details = raw_details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        code_str = f" [HTTP {self.status_code}]" if self.status_code else ""
        return f"{self.__class__.__name__}{code_str}: {self.message}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} code={self.error_code} status={self.status_code} msg='{self.message}'>"


class RazorpayConfigurationError(RazorpayClientError):
    """Raised when client environment variables or credentials are missing or invalid."""
    def __init__(self, message: str):
        super().__init__(message=message, error_code="RAZORPAY_CONFIG_ERROR")


class RazorpayAuthenticationError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 401 Unauthorized."""
    def __init__(self, message: str = "Razorpay authentication failed. Invalid API credentials."):
        super().__init__(message=message, status_code=401, error_code="AUTHENTICATION_ERROR")


class RazorpayValidationError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 400 Bad Request or invalid request body."""
    def __init__(self, message: str, raw_details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, error_code="BAD_REQUEST_ERROR", raw_details=raw_details)


class RazorpayNotFoundError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 404 Not Found."""
    def __init__(self, message: str = "Referenced payment or refund ID was not found on Razorpay."):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND_ERROR")


class RazorpayConflictError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 409 Conflict (e.g. idempotency or concurrent refund processing)."""
    def __init__(self, message: str = "Idempotency conflict or concurrent refund processing in progress.", raw_details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=409, error_code="IDEMPOTENCY_CONFLICT", raw_details=raw_details)


class RazorpayRateLimitError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 429 Too Many Requests."""
    def __init__(self, message: str = "Razorpay API rate limit exceeded. Please retry later."):
        super().__init__(message=message, status_code=429, error_code="RATE_LIMIT_ERROR")


class RazorpayServerError(RazorpayClientError):
    """Raised when Razorpay returns HTTP 500/502/503 Server Error."""
    def __init__(self, message: str = "Razorpay upstream server error.", status_code: int = 500):
        super().__init__(message=message, status_code=status_code, error_code="SERVER_ERROR")


class RazorpayTimeoutError(RazorpayClientError):
    """Raised when network call to Razorpay exceeds finite timeout."""
    def __init__(self, message: str = "Network call to Razorpay timed out."):
        super().__init__(message=message, error_code="TIMEOUT_ERROR")


class RazorpayNetworkError(RazorpayClientError):
    """Raised when connection or DNS resolution to Razorpay fails."""
    def __init__(self, message: str = "Failed to establish connection to Razorpay API base URL."):
        super().__init__(message=message, error_code="NETWORK_ERROR")
