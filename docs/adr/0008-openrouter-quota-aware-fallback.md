# ADR 0008: Stop on an Account-Wide Free-Model Daily Quota

- **Status:** Accepted
- **Date:** 2026-09-27

## Context

The required response composer tries several OpenRouter free-model routes in order. Retrying other models after an account-wide free-model daily cap cannot restore access during that quota window, while a single model or provider throttle may be recoverable through another route. OpenRouter publishes a daily request limit for free usage and notes that failed free-model requests still consume that allowance ([pricing](https://openrouter.ai/pricing/), [free inference guide](https://openrouter.ai/blog/tutorials/how-to-get-the-lowest-cost-llm-inference-on-openrouter/)). Returning the provider body would also expose unsanitized external text in the public API trace.

## Decision

On HTTP 429, inspect only a bounded set of error fields for explicit free-model daily-quota markers. An explicit model, provider, or route scope in a structured scope field or in unambiguous error wording takes precedence and means the throttle is not account-wide. Stop the model chain only when the fields identify the account-wide free-model daily cap. Continue through the configured fallback chain for model/provider-specific throttles and for unclassified 429 responses.

For the recognized account-wide cap, stop further OpenRouter attempts and pass the same controlled draft, retrieved evidence, and structured facts to the configured OpenCode Zen free-model chain. Preserve `failure_scope=account_quota` in the final `llm_refinement` event whether OpenCode succeeds or fails. If OpenCode and the supported SQLite response-template fallback cannot produce a validated answer, return the normal fail-closed 503. Do not include provider response bodies, arbitrary metadata, or credential-like values in the API response. Keep the current route-attempt metadata and status semantics for model/provider-scoped or unclassified 429s.

## Consequences

- The service avoids spending additional requests and latency on models that share a known exhausted account quota.
- Recoverable model/provider throttles still use the ordered fallback chain.
- The marker check is intentionally conservative; a new provider error shape may be treated as an ordinary 429 until covered by a regression test.
- OpenRouter calls stop immediately on the identified account cap; a configured independent provider may still complete the final composition.
- If all safe fallbacks fail, the application still withholds the controlled draft and returns HTTP 503.

## Evidence

Public `/chat` tests cover the account-wide stop and continuation after a provider throttle, structured and message-only model scopes (including a named model), and an unclassified 429 in `tests/test_app.py`.
