"""Static model bindings evidenced by the original Overchat source."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts import CapabilityId, Modality, ModelRef, ProviderHealthStatus, ProviderModelBinding


@dataclass(frozen=True, slots=True)
class OverchatModel:
    persona_id: str
    provider_model_name: str
    description: str


MODELS: tuple[OverchatModel, ...] = (
    OverchatModel(
        "gpt-5-2",
        "gpt-5.2-2025-12-11",
        "ChatGPT 5.2 (Deep Reasoning & Smart Logic)",
    ),
    OverchatModel(
        "gemini-3-5-flash",
        "google/gemini-3.5-flash",
        "Gemini Flash 3.5 (Ultra Fast Speed & Instant Response)",
    ),
    OverchatModel(
        "free-chat-gpt-landing",
        "openai/gpt-4.1-nano",
        "ChatGPT Nano (Lightweight & Free Landing Model)",
    ),
)

_MODEL_BY_PERSONA = {model.persona_id: model for model in MODELS}
_MODEL_BY_NAME = {model.provider_model_name: model for model in MODELS}


def resolve_model(model_or_persona: str) -> OverchatModel:
    """Resolve either source persona ID or provider model name exactly."""

    model = _MODEL_BY_PERSONA.get(model_or_persona) or _MODEL_BY_NAME.get(model_or_persona)
    if model is None:
        from .errors import UnsupportedModelError

        raise UnsupportedModelError(model_or_persona)
    return model


def model_refs() -> tuple[ModelRef, ...]:
    capabilities = {CapabilityId.TEXT_GENERATION, CapabilityId.STREAMING}
    return tuple(
        ModelRef(
            model_id=model.provider_model_name,
            display_name=model.description,
            capabilities=capabilities,
            modalities={Modality.TEXT},
        )
        for model in MODELS
    )


def model_bindings() -> tuple[ProviderModelBinding, ...]:
    capabilities = {CapabilityId.TEXT_GENERATION, CapabilityId.STREAMING}
    return tuple(
        ProviderModelBinding(
            provider_id="overchat",
            model_id=model.provider_model_name,
            provider_model_name=model.provider_model_name,
            capabilities=capabilities,
            availability=ProviderHealthStatus.UNKNOWN,
        )
        for model in MODELS
    )
