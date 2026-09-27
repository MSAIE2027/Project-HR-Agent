# Local Operations

## Prepare the environment

From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Keep credentials in the ignored `.env` file. Do not commit provider keys.

## Start and inspect

```bash
MSAIE_MCP_TRANSPORT=stdio ./scripts/start_local.sh --no-browser
```

The launcher loads `.env`, starts the API, waits for `/health/ready`, and streams logs. Visit `http://127.0.0.1:8000/` in a browser. Useful runtime endpoints are `/health`, `/health/ready`, `/health?deep=true`, and `/api/tools`.

The grader-facing demo and operator verification use `MSAIE_MCP_TRANSPORT=stdio` so the official MCP client launches the FastMCP server process and exercises protocol discovery/tool calls. Local development may use `inprocess` for quicker iteration; it calls the registered tool functions directly. An explicit shell value for `MSAIE_MCP_TRANSPORT` takes precedence over `.env`.

## Required answer generation

Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` locally and stores vectors in SQLite; it does not need an API key. OpenRouter at `https://openrouter.ai/api/v1` is the primary composer, trying `qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, and `google/gemma-4-26b-a4b-it:free`, then `openrouter/free`. Each OpenRouter model gets a 12-second cap. A recognized account-wide free daily quota 429 stops OpenRouter retries and routes directly to OpenCode Zen; other OpenRouter errors exhaust the chain before OpenCode. The OpenCode model chain defaults to Nemotron 3.5 Lightning Free, Big Pickle, and Space Bunny Free, with an 8-second per-model cap. These are currently listed as zero-priced, limited-time routes. OpenCode Zen otherwise bills per request, setup asks for billing details, and workspace administrators can disable model access; a valid API key or `/models` result alone does not prove that chat generation works. Set `MSAIE_LLM_API_KEY` and optionally `OPENCODE_API_KEY` in the ignored `.env`; `OPENROUTER_API_KEY` is also accepted for a legacy local setup. The OpenCode endpoint and model list are configured by `OPENCODE_ZEN_BASE_URL` and `OPENCODE_ZEN_MODELS`. Availability can change. Restart after editing the file, then check `/health` and `/health/ready`; readiness still requires the OpenRouter primary configuration. Traces show the chosen live provider/model or `status=cached_template`. The SQLite fallback stores only versioned template text and formats fresh MCP facts/citations for supported read-only PTO and positive remote-work cases; actions, unsafe/unsupported requests, and template misses still fail closed. `nvidia/nemotron-3.5-content-safety:free` is a classifier, not an answer composer. Optional remote MiniLM serving uses only the separate `MSAIE_EMBEDDING_*` variables.

## Stop

Press `Ctrl-C` in the foreground launcher. For a background service, start with `./scripts/start_local.sh --detach` and stop it with `./scripts/stop_local.sh`.
