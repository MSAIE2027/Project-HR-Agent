"""Shared default provider routes for runtime refinement and smoke evidence."""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openrouter/free"
# Metered routes lead. The project brief permits "your own API keys", and a
# credit-backed first route removes the account-wide free-daily-quota 429 that
# otherwise stops composition before a completion exists. Both entries are
# general-purpose composers; safeguard-tuned models are deliberately excluded
# because they hedge, and the answer validator requires binding status language.
OPENROUTER_METERED_MODELS = (
    "nvidia/nemotron-3-nano-30b-a3b",
    # Different model family from the first route on purpose: OpenRouter retires
    # slugs without notice, and qwen/qwen-2.5-7b-instruct began returning HTTP 404
    # on 2026-10-01 while still being listed in /api/v1/models.
    "openai/gpt-oss-120b",
)
# Zero-priced routes come last so a live answer stays reachable with no credit.
# The OpenCode Zen chain and the build-seeded SQLite templates sit after this
# provider, so removing every OpenRouter free model does not make composition
# depend on credit.
OPENROUTER_FALLBACK_MODEL = OPENROUTER_MODEL
OPENROUTER_MODEL_CHAIN = (*OPENROUTER_METERED_MODELS, OPENROUTER_FALLBACK_MODEL)

OPENCODE_ZEN_BASE_URL = "https://opencode.ai/zen/v1"
OPENCODE_ZEN_MODELS = (
    "nemotron-3.5-lightning-free",
    "big-pickle",
    "space-bunny-free",
)
OPENCODE_ZEN_FREE_MODEL_ALLOWLIST = frozenset(OPENCODE_ZEN_MODELS)
