# Overchat Capability Inventory

Source authority: `source_snapshot/01.02_overchat_gpt5_2_gemini3_5_bypass.py` (403 lines).

| Capability | Source evidence | Actual behavior | Target | Classification | Verification status |
|---|---|---|---|---|---|
| Static model catalog | `Config.available_models`, lines 58-71 | Declares three persona/model pairs; availability claims are not independently proven. | `models.py` | SUPPORTED | Deterministic catalog tests planned; live availability unverified. |
| Text generation | `send_chat_request`, lines 176-324 | Performs auth lookup, best-effort title/session initialization, then streaming response request. | `client.py`, `adapter.py` | SUPPORTED | Request and response characterization planned; live execution credential/environment limited. |
| SSE text streaming | lines 268-290 | Consumes `data:` records, concatenates `response.output_text.delta`, stops at `[DONE]`, reports server `error`, ignores malformed/unknown events. | `streaming.py` | SUPPORTED | Deterministic event-matrix tests planned. |
| Anonymous user lookup | lines 193-203 | `GET /v1/auth/me`; requires HTTP 200/201 and reads JSON `id`. No credential is supplied. | `client.py` | SUPPORTED | Transport characterization planned; upstream authorization status unverified. |
| Best-effort chat title | lines 212-223 | `PATCH` title endpoint; prompt truncated to 300 chars; all request failures ignored. | `client.py` | SUPPORTED | Ordered-call and payload tests planned. |
| Best-effort chat initialization | lines 225-235 | `POST` user chat endpoint; all request failures ignored. | `client.py` | SUPPORTED | Ordered-call and payload tests planned. |
| Mobile request headers | lines 104-125 | Sends Android/OkHttp-style content negotiation and application metadata. | `client.py` | SANITIZED | Benign content-negotiation headers retained; fabricated device identity omitted. |
| Fabricated forwarding IP/device identity | lines 100-125 | Randomizes claimed client IP and device UUID and sends spoofed identity headers. | Not executable; recorded in migration evidence only. | QUARANTINED | Blocked by V3 security rule against anti-abuse circumvention. |
| Literal `authorization: undefined` | line 263 | Sends a non-credential authorization header. | Not emitted. | SANITIZED | Security test planned. |
| Prompt file input limits | lines 152-174 | Reads UTF-8, strips content, line limit then character limit. | `io.py` | SUPPORTED | Deterministic file tests planned. |
| Reply file output | lines 308-314 | Writes full UTF-8 reply; write errors are reported but do not change returned reply. | `io.py` | SUPPORTED | Deterministic file tests planned. |
| CLI and interactive shell | lines 326-403 | Model listing/selection, direct prompt, file mode, or interactive mode. | Not a V3 provider operation. | UNSUPPORTED | Preserved in source snapshot; platform owns user interaction. |
| Retries/backoff/polling | Entire source | No retry, backoff, or polling implementation. | None | UNSUPPORTED | Static source inspection. |
| Upload/download/assets | Entire source | No asset operation. | None | UNSUPPORTED | Static source inspection. |
| Accounts/pools/session refresh | Entire source | No credential, account pool, cookie persistence, or refresh logic. | None | UNSUPPORTED | Static source inspection. |
| Provider-native agent | Entire source | No provider-agent lifecycle or tools. | None | UNSUPPORTED | Static source inspection. |
| Usage metrics | lines 178-188, 292-305 | CLI-only approximate/input/output character, line, word, token, elapsed and speed reporting. | Normalized metadata only where available. | SUPPORTED | Deterministic normalization tests planned. |

## Event matrix

| Event | Source semantics | Target representation | Classification |
|---|---|---|---|
| `response.output_text.delta` | Append non-empty `data.delta` in arrival order. | `TextDelta` and accumulated response text. | SUPPORTED |
| `error` | Print `data.message`; source continues until done/end. | `ProviderStreamError` raised with safe message. | SANITIZED (normalized failure rather than console-only error). |
| `[DONE]` | Stop reading immediately. | Iterator termination. | SUPPORTED |
| malformed JSON / unknown event / empty line | Ignore silently. | Ignore silently. | SUPPORTED |
