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

Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` locally and stores vectors in SQLite; it does not need an API key. Every citation-bearing final answer requires OpenRouter at `https://openrouter.ai/api/v1`. The service tries `qwen/qwen3.8-27b:free`, `nvidia/nemotron-3.5-lightning:free`, and `google/gemma-4-26b-a4b-it:free`, then falls back to `openrouter/free`. Each model receives one request with an 18-second cap, so the worst-case four-route wait is about 72 seconds. Set `MSAIE_LLM_API_KEY` in the ignored `.env`; `OPENROUTER_API_KEY` is also accepted for a legacy local setup. Restart after editing it, then check `/health` and `/health/ready`. Successful and failed cited answers show `llm_refinement`, the selected or failed state, attempted routes, and no unrefined draft. Missing/misconfigured settings, provider failures, and rejected model output fail closed with HTTP 503. `nvidia/nemotron-3.5-content-safety:free` is a classification model, so it is not used to compose final answers. Optional remote MiniLM serving uses only the separate `MSAIE_EMBEDDING_*` variables.

## Stop

Press `Ctrl-C` in the foreground launcher. For a background service, start with `./scripts/start_local.sh --detach` and stop it with `./scripts/stop_local.sh`.
