"""V3 facade for the isolated Overchat implementation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.contracts import (
    CapabilityId,
    Modality,
    ProviderHealth,
    ProviderHealthStatus,
    ProviderRef,
    ProviderStatus,
)

from .client import GenerationResult, OverchatClient, Transport
from .config import OverchatConfig
from .errors import OverchatError, normalize_error
from .models import model_bindings, model_refs, resolve_model


class OverchatProviderAdapter:
    provider_id = "overchat"

    def __init__(self, transport: Transport, config: OverchatConfig | None = None) -> None:
        self.client = OverchatClient(transport, config)

    @classmethod
    def with_requests(cls, config: OverchatConfig | None = None) -> "OverchatProviderAdapter":
        """Create the runtime adapter without making network calls during import."""

        try:
            import requests
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError("The Overchat runtime requires the 'requests' package.") from exc
        return cls(requests, config)

    def get_manifest(self) -> dict[str, Any]:
        return {
            "id": "overchat",
            "name": "Overchat",
            "version": "1.0.0",
            "status": "disabled",
            "is_template": False,
            "is_functional": True,
            "auth": {"types": ["anonymous"], "supports_refresh": False},
            "capabilities": {
                "text_generation": True,
                "streaming": True,
                "file_upload": False,
                "provider_agent": False,
            },
            "models": {"discovery": "static"},
        }

    def provider_ref(self) -> ProviderRef:
        return ProviderRef(
            provider_id=self.provider_id,
            display_name="Overchat",
            status=ProviderStatus.DISABLED,
            capabilities=self.get_capabilities(),
            modalities={Modality.TEXT},
            is_template=False,
            is_functional=True,
        )

    def validate_credential(self, credential_ref: str | None = None) -> ProviderHealth:
        if credential_ref:
            return ProviderHealth(
                provider_id=self.provider_id,
                status=ProviderHealthStatus.UNAVAILABLE,
                message="Overchat source does not define a credential flow.",
            )
        return ProviderHealth(
            provider_id=self.provider_id,
            status=ProviderHealthStatus.UNKNOWN,
            message="Anonymous source flow; live authorization is unverified.",
        )

    def discover_models(self):
        return model_refs()

    def discover_model_bindings(self):
        return model_bindings()

    def get_capabilities(self) -> set[CapabilityId]:
        return {CapabilityId.TEXT_GENERATION, CapabilityId.STREAMING}

    def generate_text(self, prompt: str, model: str = "gemini-3-5-flash") -> GenerationResult:
        if not isinstance(prompt, str) or not prompt:
            from .errors import ProviderResponseError

            raise ProviderResponseError("Prompt must be a non-empty string.", category="bad_request")
        return self.client.generate_text(prompt, resolve_model(model))

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_id=self.provider_id,
            status=ProviderHealthStatus.UNKNOWN,
            message="Disabled pending legitimate live verification.",
        )

    def normalize_error(self, error: Any, trace_id: str | None = None):
        return normalize_error(error, trace_id)

    @staticmethod
    def result_dict(result: GenerationResult) -> dict[str, Any]:
        return asdict(result)


__all__ = ["OverchatError", "OverchatProviderAdapter"]
