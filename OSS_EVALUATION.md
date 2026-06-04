# maivn-shared OSS Evaluation and Security Sweep

Reviewed on: 2026-06-02

Scope: `libraries/maivn-shared` source, package metadata, active package lock resolution, dependency advisory posture, license posture, Bandit static analysis, secret-pattern scan, and public package boundary review.

## Executive Summary

`maivn-shared` now has a clean OSS advisory result for the package-scoped dependency graph resolved from this checkout. The original advisory risk in `langchain-core`, `langsmith`, `orjson`, `idna`, `requests`, `urllib3`, `pytest`, and `pygments` was remediated by raising dependency floors and refreshing `uv.lock`.

The main public-boundary fixes are in place:

- Public-safe error serialization exists via `MaivnError.to_public_dict()` and `serialize_public_error()`.
- Internal exception dictionaries redact sensitive context keys and no longer include raw cause text.
- Structured logging redacts sensitive context and metadata keys.
- Tool execution result and error previews are redacted by default unless explicitly marked safe for logging.
- Prompt loading now rejects absolute paths, `..`, slash, and backslash traversal; prompt filenames must be plain Markdown filenames.
- HTTP wrapper errors no longer include raw upstream response bodies, request URLs, or raw request exception text.
- Environment parse warnings omit invalid raw values.

Current release posture: no OSS advisory blocker remains for this package-scoped graph. Remaining guardrails are usage risks: do not use internal serializers for public responses, keep generated ToolSpec descriptions under review before public/LLM exposure, and only call `load_prompt()` with trusted package names.

## Commands Run

```powershell
uv lock
uv tree --package maivn-shared --all-groups
uv export --format requirements.txt --package maivn-shared --all-groups --no-hashes --no-emit-project --no-header --no-annotate --output-file C:\Users\chad6\Documents\Codex\2026-06-02\please-do-a-full-security-sweep-4\work\maivn-shared-active-audit-requirements.txt
uvx pip-audit --progress-spinner off -r C:\Users\chad6\Documents\Codex\2026-06-02\please-do-a-full-security-sweep-4\work\maivn-shared-active-audit-requirements.txt
uvx pip-audit --progress-spinner off --vulnerability-service osv -r C:\Users\chad6\Documents\Codex\2026-06-02\please-do-a-full-security-sweep-4\work\maivn-shared-active-audit-requirements.txt
```

## Verification Results

| Check | Result |
| --- | --- |
| Package export | Resolved 302 packages. |
| PyPI `pip-audit` | Passed; no known vulnerabilities found. |
| OSV `pip-audit` | Passed; no known vulnerabilities found. |
| Targeted security regression tests | Passed; 67 tests passed. |

Full lint/type/test/Bandit verification should be run before release after any additional local edits.

## Package and Lockfile Posture

Runtime dependency floors now include explicit security floors and the direct runtime `httpx` dependency used by `src/maivn_shared/infrastructure/http_client.py`.

Runtime dependency floors:

- `httpx>=0.28.1`
- `idna>=3.15`
- `langchain-core>=1.3.3`
- `langsmith>=0.8.0`
- `orjson>=3.11.8`
- `pydantic>=2.13.3`
- `requests>=2.33.0`
- `urllib3>=2.7.0`

Development dependency floors:

- `pygments>=2.20.0`
- `pyright>=1.1.409`
- `pytest>=9.0.3`
- `ruff>=0.15.12,<1`

Active resolved package-scoped graph:

- `langchain-core==1.4.0`
- `langsmith==0.8.4`
- `orjson==3.11.8`
- `idna==3.17`
- `requests==2.33.1`
- `urllib3==2.7.0`
- `pytest==9.0.3`
- `pygments==2.20.0`
- `httpx==0.28.1`
- `pydantic==2.13.3`

## License Evaluation

No copyleft licenses were observed in the reviewed primary dependency set. The project itself is Apache-2.0, and the reviewed dependency licenses remain permissive.

| Package | Resolved version | License posture | Scope |
| --- | ---: | --- | --- |
| langchain-core | 1.4.0 | MIT | Runtime direct |
| langsmith | 0.8.4 | MIT | Runtime direct |
| orjson | 3.11.8 | Apache-2.0 OR MIT | Runtime direct |
| pydantic | 2.13.3 | MIT | Runtime direct |
| httpx | 0.28.1 | BSD | Runtime direct |
| requests | 2.33.1 | Apache-2.0 | Runtime direct |
| urllib3 | 2.7.0 | MIT | Runtime direct |
| idna | 3.17 | BSD | Runtime direct |
| PyYAML | 6.0.3 | MIT | Runtime transitive |
| jsonpatch | 1.33 | BSD | Runtime transitive |
| tenacity | 9.1.4 | Apache-2.0 | Runtime transitive |
| uuid-utils | 0.14.1 | BSD | Runtime transitive |
| zstandard | 0.25.0 | BSD-3-Clause | Runtime transitive |
| ruff | 0.15.12 | MIT | Dev |
| pytest | 9.0.3 | MIT | Dev |
| pyright | 1.1.409 | MIT | Dev |
| pygments | 2.20.0 | BSD | Dev |

OSS approval posture: acceptable for commercial/public distribution from this sweep.

## Advisory Findings

### OSS-1: Known Advisories in Runtime and Dev Graph

Status: Remediated

The active package-scoped export audits cleanly under both PyPI and OSV.

| Package | Remediated resolved version |
| --- | ---: |
| langchain-core | 1.4.0 |
| langsmith | 0.8.4 |
| orjson | 3.11.8 |
| idna | 3.17 |
| requests | 2.33.1 |
| urllib3 | 2.7.0 |
| pytest | 9.0.3 |
| pygments | 2.20.0 |

## Source Findings

### SRC-1: Public Error Serialization Can Leak Sensitive Context

Status: Remediated

Changes:

- Added `MaivnError.to_public_dict()` for client-visible error payloads.
- Added `serialize_public_error()` for generic exceptions.
- Updated `MaivnError.to_dict()` to redact context and emit cause type instead of raw cause text.
- Added regression tests proving public serializers exclude raw message text, context, args, and causes.

Residual guardrail: `serialize_error()` remains an internal diagnostic helper and still includes raw exception text. Do not use it for public API responses.

### SRC-2: HTTP Errors Include Raw Response Bodies or Request Details

Status: Remediated

Changes:

- HTTP status errors now emit `HTTP <status> response failed.` without upstream body text.
- Request and unexpected exception wrappers now include exception type, not raw exception text or request URL.
- Added regression coverage for upstream body omission and request-error text omission.

### SRC-3: Logging APIs Accept Raw Metadata and Result Previews

Status: Remediated

Changes:

- Added recursive redaction for common sensitive keys.
- Structured log context and data pass through key-based redaction before console/file formatting.
- Tool execution result and error previews default to `[REDACTED]`.
- Added `result_safe_for_log` and `error_safe_for_log` opt-ins for explicitly safe previews.
- Added regression coverage proving context, metadata, and default result previews do not leak fixture values.

Residual guardrail: message strings passed directly to logging APIs can still contain secrets if callers put secrets in the message itself. Keep secrets in structured fields so redaction can apply, or pre-redact message text at the call site.

### SRC-4: Prompt Loader Is Public and Allows Package-Adjacent File Reads

Status: Remediated for filename traversal

Changes:

- Prompt filenames are now validated as plain Markdown filenames.
- Absolute paths, `..`, slash paths, and backslash paths are rejected before import/resource lookup.
- Slash-separated package resource traversal support was removed.
- Added traversal rejection tests.

Residual guardrail: `package_name` still imports a caller-provided package. Only call `load_prompt()` with trusted package names. Internal prompt templates and LLM steering text should still live outside `maivn-shared`.

### SRC-5: Generic Serialization Walks `__dict__` and Model Dumps Without Redaction

Status: Partially remediated

Changes:

- Added `safe_public_jsonable()` for public-boundary serialization with key-based redaction.
- Kept `to_jsonable()` behavior unchanged for compatibility.

Residual guardrail: prefer schema-specific DTO serializers for public payloads. Do not use `to_jsonable()` on arbitrary internal objects for public responses.

### SRC-6: Dynamic ToolSpec Factories Can Publish Internal Documentation

Status: Accepted usage guardrail

No direct factory change was made in this sweep. The factories are useful public tooling, but generated ToolSpecs can expose function docstrings, schema descriptions, and metadata.

Required guardrail: generated ToolSpecs exposed to clients or LLMs need a pre-publication review step to strip internal descriptions, internal metadata, and sensitive field names.

### SRC-7: Environment Parsing Logs Raw Invalid Values

Status: Remediated

Changes:

- Invalid int/float warnings now log the variable name and default only.
- Added regression coverage proving invalid raw values are not recorded.

## Release Decision

Current decision: acceptable from this OSS/security sweep after remediation.

Release conditions:

1. Keep `uv.lock` synchronized with `pyproject.toml`.
2. Use `serialize_public_error()` / `MaivnError.to_public_dict()` / `safe_public_jsonable()` at public boundaries.
3. Keep `serialize_error()` and `to_jsonable()` for internal diagnostics only.
4. Review generated ToolSpecs before public/client/LLM exposure.
5. Only call `load_prompt()` with trusted package names.
