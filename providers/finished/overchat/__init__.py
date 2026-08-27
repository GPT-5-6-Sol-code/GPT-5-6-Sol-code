"""Disabled-by-default Overchat provider integration."""

from .adapter import OverchatProviderAdapter
from .client import GenerationResult, OverchatClient
from .config import OverchatConfig
from .errors import (
    OverchatError,
    ProviderResponseError,
    ProviderStreamError,
    ProviderTransportError,
    UnsupportedModelError,
)
from .models import MODELS, OverchatModel

__all__ = [
    "GenerationResult",
    "MODELS",
    "OverchatClient",
    "OverchatConfig",
    "OverchatError",
    "OverchatModel",
    "OverchatProviderAdapter",
    "ProviderResponseError",
    "ProviderStreamError",
    "ProviderTransportError",
    "UnsupportedModelError",
]
