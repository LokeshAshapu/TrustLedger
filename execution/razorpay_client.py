"""
TrustLedger Real Server-Side Razorpay Test-Mode Refund Client
Phase 11B.1 & Phase 11B.3 Razorpay Test-Mode Refund Client
"""

import base64
import json
import os
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from execution.models import RefundRequest, RefundResponse
from execution.errors import (
    RazorpayClientError,
    RazorpayConfigurationError,
    RazorpayAuthenticationError,
    RazorpayValidationError,
    RazorpayNotFoundError,
    RazorpayConflictError,
    RazorpayRateLimitError,
    RazorpayServerError,
    RazorpayTimeoutError,
    RazorpayNetworkError,
    sanitize_secret_text,
)


class RazorpayTestClient:
    """
    Production-quality server-side Razorpay Test-Mode refund client.
    Executes authorized refund requests via POST /v1/payments/:id/refund
    with HTTP Basic Auth, minor unit currency validation, and X-Refund-Idempotency.
    
    IMPORTANT: This client is SERVER-SIDE ONLY and TEST-MODE ONLY.
    It NEVER makes financial decision-gating verdicts and ONLY executes requests that have
    already passed TrustLedger verification.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_attempts: Optional[int] = None,
    ):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        raw_url = (base_url or os.getenv("RAZORPAY_BASE_URL", "https://api.razorpay.com")).rstrip("/")
        if raw_url.endswith("/v1"):
            raw_url = raw_url[:-3]
        self.base_url = raw_url
        self.timeout_seconds = float(timeout_seconds or os.getenv("RAZORPAY_TIMEOUT_SECONDS", "10.0"))
        self.max_attempts = int(max_attempts or os.getenv("RAZORPAY_MAX_ATTEMPTS", "2"))
        self.environment = os.getenv("RAZORPAY_ENVIRONMENT", "test").lower()

    def _get_auth_header(self) -> str:
        if self.environment != "test":
            raise RazorpayConfigurationError(
                f"RazorpayTestClient operates in Test Mode ONLY. RAZORPAY_ENVIRONMENT is set to '{self.environment}'. Refusing live/production execution."
            )
        if not self.key_id or not self.key_secret:
            raise RazorpayConfigurationError(
                "Razorpay API credentials missing. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in environment."
            )
        token_bytes = f"{self.key_id}:{self.key_secret}".encode("utf-8")
        auth_token = base64.b64encode(token_bytes).decode("ascii")
        return f"Basic {auth_token}"

    def health_check(self) -> Dict[str, Any]:
        """
        Discloses client health status and environment configuration.
        Does not reveal API key secrets.
        """
        has_creds = bool(self.key_id and self.key_secret)
        is_test_env = self.environment == "test"
        return {
            "client": "RazorpayTestClient",
            "environment": self.environment,
            "base_url": self.base_url,
            "timeout_seconds": self.timeout_seconds,
            "max_attempts": self.max_attempts,
            "key_status": "configured" if has_creds else "missing_credentials",
            "status": "available" if (has_creds and is_test_env) else ("unsupported_environment" if not is_test_env else "unconfigured"),
            "configured": has_creds and is_test_env,
        }

    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches payment details from GET /v1/payments/{payment_id} for preflight inspection.
        Non-mutating read-only operation.
        """
        if not payment_id or not payment_id.strip():
            raise RazorpayValidationError("payment_id must be a non-empty string.")

        auth_header = self._get_auth_header()
        endpoint_url = f"{self.base_url}/v1/payments/{payment_id.strip()}"
        headers = {"Authorization": auth_header}

        try:
            req = urllib.request.Request(endpoint_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                raise RazorpayNotFoundError(f"Payment ID '{payment_id}' not found on Razorpay Test API.")
            elif http_err.code == 401:
                raise RazorpayAuthenticationError("Invalid Razorpay API credentials.")
            else:
                raise RazorpayClientError(f"Razorpay GET payment failed with status {http_err.code}", status_code=http_err.code)
        except Exception as ex:
            raise RazorpayNetworkError(f"Failed to fetch payment: {sanitize_secret_text(str(ex))}")

    def create_refund(self, request: RefundRequest) -> RefundResponse:
        """
        Submits an idempotent refund request to POST /v1/payments/{payment_id}/refund.
        Reuses the exact request.idempotency_key across retries.
        """
        auth_header = self._get_auth_header()

        endpoint_url = f"{self.base_url}/v1/payments/{request.payment_id}/refund"

        payload = {
            "amount": request.amount_minor,
            "currency": request.currency,
        }
        if request.receipt:
            payload["receipt"] = request.receipt
        if request.notes:
            payload["notes"] = request.notes

        json_bytes = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header,
            "X-Refund-Idempotency": request.idempotency_key,
        }

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                req = urllib.request.Request(
                    endpoint_url,
                    data=json_bytes,
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)

                return self._normalize_refund_response(res_json)

            except urllib.error.HTTPError as http_err:
                # Map HTTP status codes cleanly
                err_body = http_err.read().decode("utf-8") if http_err.fp else ""
                err_json = {}
                try:
                    err_json = json.loads(err_body)
                except Exception:
                    pass

                msg = err_json.get("error", {}).get("description") or f"Razorpay API HTTP {http_err.code} Error"

                if http_err.code == 401:
                    raise RazorpayAuthenticationError(sanitize_secret_text(msg))
                elif http_err.code == 404:
                    raise RazorpayNotFoundError(sanitize_secret_text(msg))
                elif http_err.code == 409:
                    raise RazorpayConflictError(sanitize_secret_text(msg), raw_details=err_json)
                elif http_err.code == 429:
                    raise RazorpayRateLimitError(sanitize_secret_text(msg))
                elif http_err.code == 400:
                    raise RazorpayValidationError(sanitize_secret_text(msg), raw_details=err_json)
                elif http_err.code >= 500:
                    last_exception = RazorpayServerError(sanitize_secret_text(msg), status_code=http_err.code)
                    if attempt < self.max_attempts:
                        time.sleep(0.2)
                        continue
                    raise last_exception
                else:
                    raise RazorpayClientError(sanitize_secret_text(msg), status_code=http_err.code)

            except urllib.error.URLError as net_err:
                if isinstance(net_err.reason, TimeoutError) or "timed out" in str(net_err.reason).lower():
                    last_exception = RazorpayTimeoutError(f"Connection timed out after {self.timeout_seconds}s")
                else:
                    last_exception = RazorpayNetworkError(f"Network error: {sanitize_secret_text(str(net_err.reason))}")

                if attempt < self.max_attempts:
                    time.sleep(0.2)
                    continue
                raise last_exception

            except Exception as ex:
                last_exception = RazorpayClientError(sanitize_secret_text(str(ex)))
                if attempt < self.max_attempts:
                    time.sleep(0.2)
                    continue
                raise last_exception

        if last_exception:
            raise last_exception
        raise RazorpayClientError("Refund execution failed after retries.")

    def fetch_refund(self, refund_id: str) -> RefundResponse:
        """
        Fetches an existing refund record from GET /v1/refunds/{refund_id}.
        """
        if not refund_id or not refund_id.strip():
            raise RazorpayValidationError("refund_id must be a non-empty string.")

        auth_header = self._get_auth_header()
        endpoint_url = f"{self.base_url}/v1/refunds/{refund_id.strip()}"

        headers = {
            "Authorization": auth_header,
        }

        try:
            req = urllib.request.Request(endpoint_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)

            return self._normalize_refund_response(res_json)
        except urllib.error.HTTPError as http_err:
            if http_err.code == 404:
                raise RazorpayNotFoundError(f"Refund ID '{refund_id}' not found on Razorpay.")
            elif http_err.code == 401:
                raise RazorpayAuthenticationError()
            else:
                raise RazorpayClientError(f"Razorpay GET refund failed with status {http_err.code}", status_code=http_err.code)
        except Exception as ex:
            raise RazorpayNetworkError(f"Failed to fetch refund: {sanitize_secret_text(str(ex))}")

    def _normalize_refund_response(self, raw_json: Dict[str, Any]) -> RefundResponse:
        """
        Normalizes raw Razorpay API JSON response into strongly typed RefundResponse object.
        """
        return RefundResponse(
            refund_id=raw_json.get("id", "rfnd_unknown"),
            payment_id=raw_json.get("payment_id", "pay_unknown"),
            amount_minor=raw_json.get("amount", 0),
            currency=raw_json.get("currency", "INR"),
            status=raw_json.get("status", "processed"),
            receipt=raw_json.get("receipt"),
            notes=raw_json.get("notes", {}),
            created_at=raw_json.get("created_at"),
            raw_response_metadata={
                "entity": raw_json.get("entity", "refund"),
                "speed_processed": raw_json.get("speed_processed"),
                "speed_requested": raw_json.get("speed_requested"),
            },
        )
