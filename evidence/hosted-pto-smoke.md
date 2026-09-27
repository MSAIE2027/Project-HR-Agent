# Hosted PTO Smoke — Failed Closed at LLM Generation

**Date:** 2026-09-27
**Hosted SHA:** `1130dde62a5751c2fd64ee19092c2b16f7c4dfed`
**Render deploy:** `dep-das9kd59fdbs73cfutpg` (`live`)
**Service:** `https://project-hr-agent.onrender.com`
**Data:** Synthetic employee `E1001`; no real employee records were used.

## Runtime health

`GET /health/ready` and `GET /health?deep=true` returned HTTP 200. The live report showed a ready SQLite index with 14 policy documents, 182 chunks, 384-dimensional Hugging Face `sentence-transformers/all-MiniLM-L6-v2` embeddings, and all eight real MCP tools discovered over stdio. OpenRouter configuration was present. An invalid `/chat` payload returned HTTP 422 with the app's validation response.

## Hosted `/chat` attempts

| Request | Result | What it establishes |
|---|---|---|
| Synthetic PTO question for `E1001` | Client timed out at 65 seconds with no response body | No tool or model result was available to the caller. |
| Synthetic PTO retry | HTTP 502 from the public edge after about 1.2 seconds; no JSON response | No model attribution or application trace. |
| Synthetic PTO retry with a verified HTTPS client | Client timed out at 65 seconds with no response body | Hosted end-to-end path still did not complete within the client limit. |
| Policy-only PTO carry-over question | Client timed out at 55 seconds with no response body | The delay is present before the employee-balance tool sequence, or during required response generation. |
| Synthetic remote-work workflow (`E1001`, 10 days) | Client timed out at 65 seconds with no response body | The latency affects the second demo workflow as well; no hosted tool trace or resolved model was returned. |
| Synthetic PTO balance request, first instrumented retry | HTTP 503 after 79.3 seconds; JSON response | All four MCP tool calls completed; the request then failed at required OpenRouter refinement. |
| Synthetic PTO balance request, detailed retry | HTTP 503 after 69.7 seconds; JSON response | The trace completed policy search, profile lookup, PTO balance, and compliance before LLM refinement failed. Per-model outcomes are below. |
| Synthetic PTO balance and carry-over request, previous instrumented retry | HTTP 503 after 138 seconds; JSON response | All four MCP calls completed; Qwen and Gemma returned 429, Nemotron timed out, and the fallback returned an empty completion with `finish_reason=length`. No citations were returned because the request failed closed. |
| Synthetic PTO balance and carry-over request, latest instrumented retry | HTTP 503 after 73.8 seconds; JSON response | All four MCP calls completed; Qwen and Gemma returned 429, Nemotron was rejected for `unsupported_numeric_fact`, and `openrouter/free` timed out. No citations were returned because the request failed closed. |
| Short synthetic PTO balance request, previous retry | HTTP 503 after 51.7 seconds; JSON response | All four MCP calls completed; all four requested routes returned HTTP 429. No citations were returned because the request failed closed. |
| Short synthetic PTO request after cooldown | Client read timeout after 101.2 seconds; no response body | No model attempt trace reached the caller. This run does not identify whether the request was still processing or stalled. |
| Same short synthetic PTO request against the warm service | HTTP 503 after 52.9 seconds; JSON response | All four MCP calls completed; Qwen, Nemotron Lightning, Gemma, and `openrouter/free` each returned HTTP 429. No citations were returned because the request failed closed. |
| Synthetic PTO request for `E1002` after OpenRouter key replacement | HTTP 503 after 56.97 seconds; JSON response | All four MCP calls completed; `llm_refinement.status=unavailable`; all four routes were marked unavailable; no citation or model was returned. |
| Short synthetic PTO retry for `E1002` after key replacement | HTTP 503 after 64.16 seconds; JSON response | Same four MCP calls completed; all four model attempts were marked unavailable; no citation or model was returned. |

The 422 control confirms the `/chat` route is reachable. The later 503 responses prove hosted retrieval and structured-tool execution reached the OpenRouter stage, but they do not establish a successful generated answer.

### Verification after OpenRouter key replacement

On 2026-09-27, `GET /health/ready` returned HTTP 200 and reported the OpenRouter provider as configured with the expected Qwen, Nemotron Lightning, Gemma, and `openrouter/free` chain. Readiness reports that configuration is present; it does not verify that a model request will succeed.

Two public synthetic PTO requests for `E1002` reached policy search, employee lookup, PTO balance, and compliance, then returned HTTP 503 after 56.97 and 64.16 seconds. Both traces reported `llm_refinement.status=unavailable`, four model attempts marked unavailable, no citations, and no resolved model. The application withheld the unrefined draft. The public trace did not establish per-route HTTP status codes for these two attempts.

A separate minimal direct request using the local `.env` key and the pinned Qwen route returned HTTP 429. The key value and provider body were not printed or saved. HTTP 429 is not an authentication rejection, but this probe alone cannot distinguish model capacity from an account-level rate limit. The refreshed local and hosted keys therefore remain unverified for successful answer generation.

### First detailed hosted model outcomes (69.7-second retry)

The detailed retry's `llm_refinement` status was `unavailable`; no model resolved and the API correctly returned its fail-closed 503 response. Sanitized per-model outcomes:

| Requested model | Outcome |
|---|---|
| `qwen/qwen3.8-27b:free` | HTTP 429 |
| `nvidia/nemotron-3.5-lightning:free` | Provider request timed out |
| `google/gemma-4-26b-a4b-it:free` | HTTP 429 |
| `openrouter/free` | Rejected malformed provider response: one choice, no text content, `finish_reason=length` |

### Hosted model outcomes (73.8-second retry)

The newest `llm_refinement` status was `unavailable`; all outcomes are sanitized:

| Requested model | Outcome |
|---|---|
| `qwen/qwen3.8-27b:free` | HTTP 429 |
| `nvidia/nemotron-3.5-lightning:free` | Response rejected: `unsupported_numeric_fact` |
| `google/gemma-4-26b-a4b-it:free` | HTTP 429 |
| `openrouter/free` | Provider request timed out |

### Previous hosted model outcomes (51.7-second retry)

All four route attempts returned HTTP 429. A separate minimal direct request to the pinned InclusionAI route also returned HTTP 429 with a generic rate-limit message. The response had no `Retry-After` header and no provider/account details, so this evidence does not identify whether the limit is model-provider capacity or the OpenRouter account tier.

No answer text, credentials, or provider error body is stored. Render's recent metrics sample showed a 449.2 MB peak against a 536.9 MB memory limit; this is a possible resource-pressure clue, not proof that memory caused the provider failures. Render returned no HTTP latency samples for this service.

### Latest hosted model outcomes (52.9-second retry)

The warmed retry returned HTTP 503 with `llm_refinement.status=unavailable`. Each configured model route returned HTTP 429; no route resolved, no citations were returned, and the app failed closed. Immediately before this retry, a separate client request timed out at 101.2 seconds without receiving an application response, so no trace from that request was available. The health endpoints still return HTTP 200 with the local Hugging Face/SQLite index and MCP tools ready. This confirms the current release can execute its complete MCP workflow, but the current provider route set remains unavailable on the hosted account.

### Direct synthetic output-budget diagnostic

To isolate the empty/truncated completions, the local configured key was used for direct OpenRouter requests with fictional PTO facts only. At `max_tokens=500`, Qwen and Gemma again returned 429; Nemotron returned `finish_reason=length`, and one `openrouter/free` selection returned no `content` with the same finish reason. At `max_tokens=1000`, the pinned Nemotron request returned a completed response (`finish_reason=stop`), and `openrouter/free` also returned final text on that request. Qwen and Gemma still returned 429. A separate `reasoning_effort=none` probe let Nemotron and one free-route selection complete at 500 tokens with no separate reasoning field, although a full-prompt response still triggered numeric validation. The most useful full-prompt check pinned `inclusionai/ling-3.0-flash-fin:free`, used the app's `build_grounding_prompt`, and ran its `_refinement_issue` validator: at 1,000 tokens it returned no final text; at 2,000 tokens it returned `finish_reason=stop` in 1.67 seconds and the validator returned no issue. The prompt also explicitly told the model not to repeat document IDs or chunk IDs. This is a direct composer probe, not an MCP-backed `/chat` run, and no generated text is retained. `openrouter/free` selected different underlying models across calls, so its samples are not controlled comparisons. A separate sample rendered the policy's spelled-out `twenty` as `20`; the validator now treats spelled-out policy quantities with recognized units as equivalent to digits, with public `/chat` coverage for both supported `20` and unsupported `21`.

Two more direct calls used the configured key, five passages from the local SQLite index, the app prompt builder, and synthetic PTO content. A pinned `inclusionai/ling-3.0-flash-fin:free` call using the current system instruction and 500-token cap completed in 3.06 seconds and passed `_refinement_issue`; a second call with an added no-source-ID instruction and 2,000-token cap completed in 2.05 seconds but was rejected as `unsupported_numeric_fact`. These are controlled direct-composer diagnostics only: they do not prove `/chat` reliability, and the second rejection's raw completion was not retained. No credentials or generated answer text are stored.

The ID issue was then isolated without retaining model text. After removing document ID, chunk ID, and source path metadata lines from the same five-citation grounding prompt, three consecutive pinned `inclusionai/ling-3.0-flash-fin:free` calls at 2,000 tokens completed in 1.3–3.3 seconds; all passed `_refinement_issue`, had no known reasoning marker, no internal ID marker, and no unsupported numeric token. A further three calls to that pinned route passed five policy-fidelity checks each: the five-day cap, written HR approval, documented reason, carried-days ordering, and no inference of balance composition. This is the strongest direct-composer evidence so far for removing internal identifiers from the LLM prompt while retaining citation metadata in the API/UI response. It remains direct OpenRouter testing, not an end-to-end `/chat` acceptance run. The official [OpenRouter model page](https://openrouter.ai/inclusionai/ling-3.0-flash-fin:free) currently lists this route as free and describes it as finance-focused; it may be tested as an explicit route, with the domain mismatch considered during model selection. A separate three-request probe of `inclusionai/ling-3.0-flash:free` returned HTTP 404 each time, so do not assume the related generic alias is callable merely because the finance variant resolved through `openrouter/free`.

Three direct calls to the dynamic `openrouter/free` route at 2,000 tokens resolved to three different models. Only the `inclusionai/ling-3.0-flash-sante:free` response passed the current validator; two Nemotron responses omitted required numeric facts. This demonstrates why a free-router result must be evaluated and why a specific model route is preferable for reproducible demo behavior. These calls used no internal ID lines and were still only composer probes.

## Local synthetic PTO diagnostic

A local `TestClient` request used the project's `.env` without printing or saving credentials, the 182-chunk local SQLite index, and the real stdio MCP subprocess. It completed the following tool sequence, then failed closed with HTTP 503 after 27.9 seconds:

`search_policy_documents` → `lookup_employee_profile` → `check_pto_balance` → `check_policy_compliance`

The configured response route order was attempted:

| Requested route | Outcome |
|---|---|
| `qwen/qwen3.8-27b:free` | HTTP 429 |
| `nvidia/nemotron-3.5-lightning:free` | Rejected: `unsupported_numeric_fact` |
| `google/gemma-4-26b-a4b-it:free` | HTTP 429 |
| `openrouter/free` | Rejected: `numeric_fact_omitted` |

No route completed a validated PTO answer, so there is no resolved model to report for this request. The app did not return its unrefined policy draft. Raw model text and credentials are intentionally absent from this artifact.

### Current working-tree request after key replacement

A local synthetic PTO request for `E1002` was sent through the current working-tree app, the 182-chunk SQLite index, and the real stdio MCP server. It returned HTTP 503 in 10.72 seconds after `search_policy_documents`, `lookup_employee_profile`, `check_pto_balance`, and `check_policy_compliance`. All four configured OpenRouter routes returned HTTP 429; there were no citations or resolved model because the app withheld its draft. The response status was `llm_unavailable`. Only status and sanitized route metadata were retained; no completion text or credential was saved.

## Later local PTO success

A second local synthetic PTO request completed on the same 182-chunk SQLite index, using the real stdio MCP subprocess and the local `.env` without displaying credentials. It returned HTTP 200 in 26.73 seconds with status `completed`, five `POL-PTO-01` citations, and this MCP sequence:

`search_policy_documents` → `lookup_employee_profile` → `check_pto_balance` → `check_policy_compliance`

`llm_refinement.status=completed`. The requested route that completed was `openrouter/free`; the actual resolved model was `inclusionai/ling-3.0-flash-fin:free`. The same request again saw Qwen and Gemma return 429 and Nemotron fail numeric validation before the fallback succeeded. The output passed the then-current marker set, but its raw generated text was not retained and cannot be rechecked against the strengthened process-narration guard added later. Raw generated text and credentials are not stored.

This identifies the model for this **local synthetic PTO response only**. It does not establish which model a future request or the hosted Render service will use. The hosted retries now confirm that the same configured chain is reached, but it has not produced a validated response there.

## Latest local real-stdio diagnostic

A separate local orchestration run used the real spawned stdio MCP server for synthetic employee `E1001`. It completed `search_policy_documents`, `lookup_employee_profile`, `check_pto_balance`, and `check_policy_compliance`, returning five policy citations and structured PTO facts. A direct pinned completion request then returned HTTP 429 from OpenRouter, so this diagnostic did not produce a model answer. Together with the earlier successful local `/chat` request, this confirms the local SQLite/MCP/OpenRouter path is wired; it does not resolve the hosted failure or identify a model for a failed request.

## Latency clue

A local, fresh stdio MCP process discovered the eight tools in 1.3 seconds; its first Hugging Face dense policy search took 10.4 seconds while the child process loaded `sentence-transformers/all-MiniLM-L6-v2`. The current web request opens a fresh stdio process per chat. This is a concrete cold-path cost to address and measure; it does not alone explain the hosted timeouts and provider 429 responses.

## Gate

The deployment is live and health-checked, but it is not ready for a recorded end-to-end demo. A local PTO response succeeded earlier with resolved model `inclusionai/ling-3.0-flash-fin:free`. After the key replacement, two hosted synthetic PTO requests still returned HTTP 503 after all four model attempts were marked unavailable; neither returned citations or a resolved model. Earlier hosted requests include the 52.9-second 429 retry and a client timeout after 101.2 seconds. Local `/chat` tests now cover citation-metadata separation, supported word-to-digit normalization, rejection of unsupported numbers, process-narration leaks, mixed employee ID/name comparisons, and medical-file requests. These safeguards have not yet been deployed or verified against a live hosted answer. Keep testing synthetic hosted requests until a new tested SHA returns HTTP 200, includes `check_pto_balance` and citations, records `llm_refinement.status=completed` with the actual resolved model, and passes the strengthened reasoning-output gate.
