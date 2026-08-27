# Overchat Exact Source-to-Target Map

| Source responsibility | Source symbol/lines | Target | Adaptation |
|---|---|---|---|
| Configuration and static model aliases | `Config`, 51-92 | `config.py`, `models.py` | Dataclass split from immutable model catalog; values retained. |
| Random fake IP generation | `generate_fake_ip`, 100-102 | Evidence only | Quarantined; anti-abuse/evasion behavior is not executable. |
| Mobile headers and random identity | `build_mobile_headers`, 104-125 | `client.py:build_headers` | Retains benign HTTP negotiation/app headers; removes claimed forwarding IP, fabricated hardware identity, and literal undefined authorization. |
| Banner/statistics display | `print_banner`, 127-150; stats in 178-189 and 292-306 | Adapter result metadata where contract-relevant | Presentation is excluded; observable counts are normalized. |
| File input and filtering | `read_input_content`, 152-174 | `io.py:read_input_content` | Same strip, line-first, character-second behavior. |
| Auth/user lookup | `send_chat_request`, 193-203 | `client.py:get_user_id` | Same GET path, 15-second timeout, accepted statuses; missing ID becomes normalized bad response. |
| Chat title request | lines 212-223 | `client.py:generate_chat_title` | Same endpoint/payload/truncation/timeout and best-effort suppression. |
| Chat initialization | lines 225-235 | `client.py:create_chat` | Same endpoint/payload/timeout and best-effort suppression. |
| Response request | lines 241-269 | `client.py:stream_chat` | Same endpoint, payload fields, stream flag, request order, configured timeout. |
| SSE parser | lines 271-290 | `streaming.py:iter_sse_events`, `collect_text` | Same delta concatenation, done handling, malformed/unknown ignore behavior; server errors normalized. |
| HTTP/status/transport errors | lines 195-203, 271-324 | `errors.py`, `adapter.py` | Console/`None` failures become stable normalized provider exceptions. |
| Reply output | lines 308-314 | `io.py:write_output` | Same UTF-8 full-response write; adapter does not write unless explicitly requested. |
| Interactive and CLI orchestration | lines 326-403 | Source snapshot only | Not a provider operation; platform owns interaction and routing. |
| V3 facade | No source equivalent | `adapter.py:OverchatProviderAdapter` | Mechanical boundary exposing manifest, models, capabilities, health, generation, and normalized errors. |
| Provider declaration | No source equivalent | `manifest.yaml` | Mechanical V3 metadata; disabled pending legitimate live verification. |

## Execution graph

`OverchatProviderAdapter.generate_text` → validate model/persona → `OverchatClient.generate_text` → anonymous user lookup → best-effort title request → best-effort chat initialization → streaming response request → SSE normalization → normalized text response.

There is no credential, account pool, retry, backoff, polling, file upload/download, tool, or provider-agent path in the source.
