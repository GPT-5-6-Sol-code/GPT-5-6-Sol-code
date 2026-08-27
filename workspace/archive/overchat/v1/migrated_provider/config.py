"""Overchat provider configuration derived from the supplied source."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OverchatConfig:
    """Runtime values preserved from the original provider."""

    base_url: str = "https://api.overchat.ai"
    timeout_seconds: int = 120
    setup_timeout_seconds: int = 15
    system_prompt: str = (
        "You are an expert AI assistant. "
        "Provide accurate, structured, and well-reasoned responses. "
        "Reply in Egyptian Arabic when requested or appropriate."
    )
