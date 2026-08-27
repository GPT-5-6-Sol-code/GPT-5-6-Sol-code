"""SSE parsing faithful to the supplied Overchat implementation."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable, Iterator

from .errors import ProviderStreamError


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


def _decode_line(line: bytes | str) -> str:
    if isinstance(line, bytes):
        return line.decode("utf-8", errors="replace")
    return line


def iter_text_deltas(lines: Iterable[bytes | str]) -> Iterator[TextDelta]:
    """Yield source-supported text deltas in provider order.

    Empty lines, malformed JSON, and unknown events are intentionally ignored.
    A provider error event is normalized instead of being printed and hidden.
    """

    for raw_line in lines:
        if not raw_line:
            continue
        line = _decode_line(raw_line)
        if not line.startswith("data:"):
            continue
        payload = line.replace("data: ", "", 1).strip()
        if payload == "[DONE]":
            return
        try:
            event = json.loads(payload)
        except (TypeError, ValueError):
            continue
        event_type = event.get("event")
        data = event.get("data")
        if not isinstance(data, dict):
            data = {}
        if event_type == "response.output_text.delta":
            delta = data.get("delta", "")
            if delta:
                yield TextDelta(str(delta))
        elif event_type == "error":
            message = data.get("message")
            raise ProviderStreamError(str(message) if message else "Overchat stream returned an error.")


def collect_text(lines: Iterable[bytes | str]) -> str:
    return "".join(delta.text for delta in iter_text_deltas(lines))
