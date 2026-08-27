# Overchat Migration Plan

## Target package

```text
providers/finished/overchat/
  __init__.py
  adapter.py
  client.py
  config.py
  errors.py
  io.py
  models.py
  streaming.py
  manifest.yaml
  tests/
```

The finished package will have no runtime import or path dependency on `workspace/working`.

## Behavior preservation

- Preserve static persona/model pairs exactly as source data.
- Preserve request endpoint paths, methods, order, payload values, title truncation, accepted success statuses, and timeouts.
- Preserve best-effort title and chat initialization semantics.
- Preserve ordered SSE delta concatenation, `[DONE]` termination, and malformed/unknown event tolerance.
- Preserve UTF-8 file filtering order and complete reply writes.

## Mechanical V3 adaptations

- Put provider-specific transport and parsing inside the provider package.
- Add an adapter facade, explicit capabilities, health, and normalized errors.
- Inject an HTTP transport so deterministic tests do not contact the provider.
- Return structured responses rather than printing UI text or returning `None`.
- Keep the provider disabled until legitimate live verification is available.

## Security sanitization and quarantine

- Do not emit fabricated `X-Forwarded-For`, `X-Real-IP`, or `Client-IP` values.
- Do not fabricate hardware/device identity for anti-abuse evasion.
- Do not emit literal `authorization: undefined`.
- Retain the exact original source only in the auditable source snapshot.
- Do not copy credentials, cookies, or private runtime state (none are present in supplied source).

## Unsupported/unknown behavior

- No retries, backoff, polling, account pool, session refresh, upload/download, tool use, or provider-agent behavior will be invented.
- Upstream model availability, anonymous-access authorization, quotas, and rate limits remain unknown without legitimate live evidence.
- CLI presentation remains outside the provider contract.

## Verification

1. Characterize source constants and call semantics using an injected fake `requests` module.
2. Test target request method/path/order/payload semantics with an injected recording transport.
3. Differentially compare source and target safe request behavior and SSE output.
4. Test malformed SSE, server error events, HTTP failures, missing user ID, timeouts, and unsupported models.
5. Test file limits and output handling.
6. Verify manifest, disabled activation, capabilities, static models, health, and error normalization.
7. Run all contract tests and repository verification.
8. Clean caches, temporarily make `workspace/working/overchat` unavailable, and run finished-package tests.
9. Run secret/evasion-header scans on portable artifacts.

## Live verification

Live execution will be attempted only if it does not require circumvention or private credentials. Absence of legitimate authorization and inability to establish upstream permission will be recorded as an environmental/security limitation rather than replaced by mock claims.

## Archive plan

After final validation, create a new immutable `workspace/archive/overchat/v1/` containing the exact source snapshot, migrated provider, manifest, planning/evidence reports, and independently reproducible hashes. Never overwrite an existing revision.
