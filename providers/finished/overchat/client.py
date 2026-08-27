"""Provider-local Overchat HTTP request flow."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Iterable, Protocol
from uuid import uuid4

from .config import OverchatConfig
from .errors import ProviderTransportError, from_http_status
from .models import OverchatModel
from .streaming import collect_text


class ResponseLike(Protocol):
    status_code: int
    text: str

    def json(self) -> dict[str, Any]: ...

    def iter_lines(self) -> Iterable[bytes | str]: ...


class Transport(Protocol):
    def get(self, url: str, **kwargs: Any) -> ResponseLike: ...

    def patch(self, url: str, **kwargs: Any) -> ResponseLike: ...

    def post(self, url: str, **kwargs: Any) -> ResponseLike: ...


@dataclass(frozen=True, slots=True)
class GenerationResult:
    text: str
    persona_id: str
    model: str
    chat_id: str


def build_headers(*, json_content: bool = False, stream: bool = False) -> dict[str, str]:
    """Build sanitized headers without fabricated client/network identity."""

    headers = {
        "User-Agent": "general-ai-core-overchat-provider/1.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip",
        "x-app-build-number": "80",
        "x-app-version": "1.0",
        "x-app-default-lang": "ar",
    }
    if json_content:
        headers["Content-Type"] = "application/json"
    if stream:
        headers.update(
            {
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                "cache-control": "no-cache",
                "x-requested-with": "XMLHttpRequest",
            }
        )
    return headers


class OverchatClient:
    """Faithful request sequence with transport injection for verification."""

    def __init__(self, transport: Transport, config: OverchatConfig | None = None) -> None:
        self.transport = transport
        self.config = config or OverchatConfig()

    def _url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}{path}"

    def get_user_id(self) -> Any:
        try:
            response = self.transport.get(
                self._url("/v1/auth/me"),
                headers=build_headers(),
                timeout=self.config.setup_timeout_seconds,
            )
        except Exception as exc:
            raise ProviderTransportError("Overchat user lookup failed.") from exc
        if response.status_code not in {200, 201}:
            raise from_http_status(response.status_code, "user lookup")
        try:
            return response.json().get("id")
        except Exception as exc:
            raise ProviderTransportError("Overchat user lookup returned invalid JSON.") from exc

    def generate_chat_title(self, user_id: Any, chat_id: str, prompt: str, model: OverchatModel) -> None:
        payload = {
            "userPrompt": prompt[:300],
            "systemPrompt": self.config.system_prompt,
            "personaType": "text",
            "personaModel": model.provider_model_name,
        }
        try:
            self.transport.patch(
                self._url(f"/v1/chat/{user_id}/{chat_id}/generateChatTitle"),
                data=json.dumps(payload),
                headers=build_headers(json_content=True),
                timeout=self.config.setup_timeout_seconds,
            )
        except Exception:
            pass

    def create_chat(self, user_id: Any, chat_id: str, model: OverchatModel) -> None:
        payload = {
            "personaId": model.persona_id,
            "firstBotMessageHidden": True,
            "chatUuid": chat_id,
        }
        try:
            self.transport.post(
                self._url(f"/v1/chat/{user_id}"),
                data=json.dumps(payload),
                headers=build_headers(json_content=True),
                timeout=self.config.setup_timeout_seconds,
            )
        except Exception:
            pass

    def stream_chat(self, prompt: str, model: OverchatModel, chat_id: str) -> str:
        payload = {
            "messages": [
                {"role": "user", "content": prompt, "id": str(uuid4())},
                {"id": str(uuid4()), "role": "system", "content": ""},
            ],
            "model": model.provider_model_name,
            "personaId": model.persona_id,
            "chatId": chat_id,
            "frequency_penalty": 0,
            "max_tokens": 4000,
            "presence_penalty": 0,
            "stream": True,
            "temperature": 0.5,
            "top_p": 0.95,
        }
        try:
            response = self.transport.post(
                self._url("/v2/chat/responses"),
                data=json.dumps(payload),
                headers=build_headers(stream=True),
                stream=True,
                timeout=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise ProviderTransportError("Overchat response request failed.") from exc
        if response.status_code not in {200, 201}:
            raise from_http_status(response.status_code, "response request")
        return collect_text(response.iter_lines())

    def generate_text(self, prompt: str, model: OverchatModel) -> GenerationResult:
        user_id = self.get_user_id()
        chat_id = str(uuid4())
        self.generate_chat_title(user_id, chat_id, prompt, model)
        self.create_chat(user_id, chat_id, model)
        text = self.stream_chat(prompt, model, chat_id)
        return GenerationResult(
            text=text,
            persona_id=model.persona_id,
            model=model.provider_model_name,
            chat_id=chat_id,
        )
