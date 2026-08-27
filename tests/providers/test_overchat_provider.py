from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import types
from typing import Any

import pytest

from core.contracts import CapabilityId, ErrorCode, ProviderHealthStatus, ProviderStatus
from providers.finished.overchat import OverchatProviderAdapter
from providers.finished.overchat.errors import ProviderStreamError, from_http_status
from providers.finished.overchat.io import read_input_content, write_output
from providers.finished.overchat.models import MODELS, resolve_model
from providers.finished.overchat.streaming import collect_text


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "workspace/inbox/gemini--flash/01.02_overchat_gpt5_2_gemini3_5_bypass.py"


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, lines=(), text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._lines = list(lines)
        self.text = text

    def json(self):
        return self._json_data

    def iter_lines(self):
        return iter(self._lines)


class RecordingTransport:
    def __init__(self, *, stream_status=200, lines=None, fail_setup=False):
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.post_count = 0
        self.stream_status = stream_status
        self.lines = lines or [
            b'data: {"event":"response.output_text.delta","data":{"delta":"hello "}}',
            b"data: not-json",
            b'data: {"event":"unknown","data":{}}',
            b'data: {"event":"response.output_text.delta","data":{"delta":"world"}}',
            b"data: [DONE]",
            b'data: {"event":"response.output_text.delta","data":{"delta":"ignored"}}',
        ]
        self.fail_setup = fail_setup

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return FakeResponse(json_data={"id": "user-1"})

    def patch(self, url, **kwargs):
        self.calls.append(("PATCH", url, kwargs))
        if self.fail_setup:
            raise RuntimeError("ignored title failure")
        return FakeResponse()

    def post(self, url, **kwargs):
        self.post_count += 1
        self.calls.append(("POST", url, kwargs))
        if self.post_count == 1:
            if self.fail_setup:
                raise RuntimeError("ignored create failure")
            return FakeResponse()
        return FakeResponse(self.stream_status, lines=self.lines)


def load_original(tmp_path: Path):
    module_name = "overchat_original_characterization"
    module = types.ModuleType(module_name)
    module.__file__ = str(SOURCE)
    source_code = compile(SOURCE.read_bytes(), str(SOURCE), "exec")
    sys.modules[module_name] = module
    try:
        exec(source_code, module.__dict__)
    finally:
        sys.modules.pop(module_name, None)
    module.BASE_DIR = tmp_path
    return module


def semantic_calls(calls):
    result = []
    for method, url, kwargs in calls:
        payload = json.loads(kwargs["data"]) if "data" in kwargs else None
        if payload and "messages" in payload:
            payload = dict(payload)
            payload["messages"] = [
                {key: value for key, value in message.items() if key != "id"}
                for message in payload["messages"]
            ]
        result.append((method, url.split("api.overchat.ai", 1)[-1], payload))
    return result


def test_source_identity_is_locked():
    assert SOURCE.stat().st_size == 20308
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == (
        "d513c0359c8aada2801a3d847466cf2d0e865e33fd05f0d180c902187cbbc470"
    )


def test_manifest_and_v3_contracts_are_disabled_and_explicit():
    adapter = OverchatProviderAdapter(RecordingTransport())
    manifest = adapter.get_manifest()
    assert manifest["status"] == "disabled"
    assert manifest["auth"]["types"] == ["anonymous"]
    assert manifest["capabilities"] == {
        "text_generation": True,
        "streaming": True,
        "file_upload": False,
        "provider_agent": False,
    }
    ref = adapter.provider_ref()
    assert ref.status is ProviderStatus.DISABLED
    assert ref.capabilities == {CapabilityId.TEXT_GENERATION, CapabilityId.STREAMING}
    assert adapter.health_check().status is ProviderHealthStatus.UNKNOWN
    assert adapter.validate_credential().status is ProviderHealthStatus.UNKNOWN
    assert adapter.validate_credential("secret-ref").status is ProviderHealthStatus.UNAVAILABLE


def test_static_model_catalog_exactly_matches_source_values():
    assert [(item.persona_id, item.provider_model_name) for item in MODELS] == [
        ("gpt-5-2", "gpt-5.2-2025-12-11"),
        ("gemini-3-5-flash", "google/gemini-3.5-flash"),
        ("free-chat-gpt-landing", "openai/gpt-4.1-nano"),
    ]
    assert resolve_model("google/gemini-3.5-flash").persona_id == "gemini-3-5-flash"
    with pytest.raises(Exception, match="Unsupported Overchat model"):
        resolve_model("invented-model")


def test_sse_event_matrix_preserves_delta_order_done_and_tolerance():
    lines = [
        b"",
        b"event: ignored",
        b"data: malformed",
        b'data: {"event":"response.output_text.delta","data":{"delta":"A"}}',
        b'data: {"event":"response.output_text.delta","data":{"delta":""}}',
        b'data: {"event":"other","data":{"delta":"X"}}',
        b"data: [DONE]",
        b'data: {"event":"response.output_text.delta","data":{"delta":"B"}}',
    ]
    assert collect_text(lines) == "A"


def test_server_error_event_is_normalized():
    lines = [b'data: {"event":"error","data":{"message":"safe failure"}}']
    with pytest.raises(ProviderStreamError, match="safe failure"):
        collect_text(lines)


def test_safe_request_flow_is_semantically_differential_to_original(tmp_path):
    prompt = "x" * 350
    source_transport = RecordingTransport()
    source = load_original(tmp_path)
    source.requests = source_transport
    source_cfg = source.Config(output_file="reply.txt")
    with redirect_stdout(io.StringIO()):
        source_result = source.send_chat_request(prompt, source_cfg, "test")

    target_transport = RecordingTransport()
    target_result = OverchatProviderAdapter(target_transport).generate_text(
        prompt, "gemini-3-5-flash"
    )

    assert source_result == target_result.text == "hello world"
    assert (tmp_path / "reply.txt").read_text(encoding="utf-8") == "hello world"

    source_calls = semantic_calls(source_transport.calls)
    target_calls = semantic_calls(target_transport.calls)
    assert [item[0] for item in source_calls] == ["GET", "PATCH", "POST", "POST"]
    assert [item[0] for item in target_calls] == ["GET", "PATCH", "POST", "POST"]
    for calls in (source_calls, target_calls):
        assert calls[0][1] == "/v1/auth/me"
        assert calls[1][1].startswith("/v1/chat/user-1/")
        assert calls[1][1].endswith("/generateChatTitle")
        assert calls[2][1] == "/v1/chat/user-1"
        assert calls[3][1] == "/v2/chat/responses"
        chat_id = calls[1][1].removeprefix("/v1/chat/user-1/").removesuffix(
            "/generateChatTitle"
        )
        assert calls[2][2]["chatUuid"] == chat_id
        assert calls[3][2]["chatId"] == chat_id
    assert source_calls[1][2]["userPrompt"] == target_calls[1][2]["userPrompt"] == prompt[:300]
    assert source_calls[1][2]["personaModel"] == target_calls[1][2]["personaModel"]
    assert source_calls[2][2]["personaId"] == target_calls[2][2]["personaId"]
    for key in (
        "model",
        "personaId",
        "frequency_penalty",
        "max_tokens",
        "presence_penalty",
        "stream",
        "temperature",
        "top_p",
    ):
        assert source_calls[3][2][key] == target_calls[3][2][key]
    assert source_calls[3][2]["messages"] == target_calls[3][2]["messages"]


def test_setup_failures_remain_best_effort():
    transport = RecordingTransport(fail_setup=True)
    result = OverchatProviderAdapter(transport).generate_text("hello")
    assert result.text == "hello world"
    assert [method for method, _, _ in transport.calls] == ["GET", "PATCH", "POST", "POST"]


def test_security_sanitization_blocks_evasion_headers():
    transport = RecordingTransport()
    OverchatProviderAdapter(transport).generate_text("hello")
    forbidden = {"x-forwarded-for", "x-real-ip", "client-ip", "x-device-uuid", "authorization"}
    for _, _, kwargs in transport.calls:
        header_names = {name.lower() for name in kwargs["headers"]}
        assert not header_names.intersection(forbidden)
        assert kwargs["headers"]["User-Agent"] == "general-ai-core-overchat-provider/1.0"


def test_http_error_normalization_is_retry_aware():
    adapter = OverchatProviderAdapter(RecordingTransport(stream_status=429))
    with pytest.raises(Exception) as captured:
        adapter.generate_text("hello")
    normalized = adapter.normalize_error(captured.value, trace_id="trace-1")
    assert normalized.code is ErrorCode.RATE_LIMITED
    assert normalized.retryable is True
    assert normalized.trace_id == "trace-1"
    assert from_http_status(503, "test").retryable is True


def test_file_filtering_and_output_match_source_order(tmp_path):
    input_path = tmp_path / "input.txt"
    input_path.write_text("  first\nsecond\nthird  ", encoding="utf-8")
    assert read_input_content(input_path, max_lines=2, max_chars=8) == "first\nse"
    assert read_input_content(tmp_path / "missing.txt") == ""
    output_path = tmp_path / "output.txt"
    write_output(output_path, "مرحبا")
    assert output_path.read_text(encoding="utf-8") == "مرحبا"
