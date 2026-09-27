"""Shared default provider routes for runtime refinement and smoke evidence."""

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openrouter/free"
OPENROUTER_PRIMARY_MODELS = (
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
)
OPENROUTER_FALLBACK_MODEL = OPENROUTER_MODEL
OPENROUTER_MODEL_CHAIN = (*OPENROUTER_PRIMARY_MODELS, OPENROUTER_FALLBACK_MODEL)

OPENCODE_ZEN_BASE_URL = "https://opencode.ai/zen/v1"
OPENCODE_ZEN_MODELS = (
    "nemotron-3.5-lightning-free",
    "big-pickle",
    "space-bunny-free",
)
OPENCODE_ZEN_FREE_MODEL_ALLOWLIST = frozenset(OPENCODE_ZEN_MODELS)
