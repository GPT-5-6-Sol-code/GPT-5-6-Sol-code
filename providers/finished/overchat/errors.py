"""Provider-local errors and V3 normalization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.contracts import ErrorCode, ErrorDetail, ErrorResponse


@dataclass(frozen=True, slots=True)
class OverchatError(Exception):
    message: str
    category: str = "non_retryable_error"
    retryable: bool = False
    provider_code: str | None = None
    retry_after_ms: int | None = None

    def __str__(self) -> str:
        return self.message


class UnsupportedModelError(OverchatError):
    def __init__(self, model: str) -> None:
        super().__init__(
            f"Unsupported Overchat model or persona: {model}",
            category="model_unavailable",
        )


class ProviderTransportError(OverchatError):
    def __init__(self, message: str = "Overchat transport failed.") -> None:
        super().__init__(message, category="provider_unavailable", retryable=True)


class ProviderResponseError(OverchatError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
        category: str = "non_retryable_error",
    ) -> None:
        super().__init__(
            message,
            category=category,
            retryable=retryable,
            provider_code=str(status_code) if status_code is not None else None,
        )


class ProviderStreamError(OverchatError):
    def __init__(self, message: str = "Overchat stream returned an error.") -> None:
        super().__init__(message, category="non_retryable_error")


def _status_category(status_code: int) -> tuple[str, bool]:
    if status_code in {401, 403}:
        return "invalid_credential", False
    if status_code == 429:
        return "rate_limited", True
    if status_code == 404:
        return "model_unavailable", False
    if status_code >= 500:
        return "retryable_server_error", True
    return "bad_request", False


def from_http_status(status_code: int, operation: str) -> ProviderResponseError:
    category, retryable = _status_category(status_code)
    return ProviderResponseError(
        f"Overchat {operation} failed with HTTP {status_code}.",
        status_code=status_code,
        retryable=retryable,
        category=category,
    )


def normalize_error(error: Any, trace_id: str | None = None) -> ErrorResponse:
    """Map provider details to the repository's stable public error contract."""

    if not isinstance(error, OverchatError):
        error = ProviderTransportError()
    code_by_category = {
        "invalid_credential": ErrorCode.UNAUTHENTICATED,
        "rate_limited": ErrorCode.RATE_LIMITED,
        "model_unavailable": ErrorCode.MODEL_UNAVAILABLE,
        "provider_unavailable": ErrorCode.PROVIDER_UNAVAILABLE,
        "retryable_server_error": ErrorCode.PROVIDER_UNAVAILABLE,
        "bad_request": ErrorCode.VALIDATION_ERROR,
    }
    details = [ErrorDetail(field="category", reason=error.category)]
    if error.provider_code:
        details.append(ErrorDetail(field="provider_code", reason=error.provider_code))
    return ErrorResponse(
        code=code_by_category.get(error.category, ErrorCode.EXECUTION_FAILED),
        message=error.message,
        retryable=error.retryable,
        trace_id=trace_id,
        details=details,
    )
