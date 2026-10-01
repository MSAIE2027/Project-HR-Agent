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

Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` locally and stores vectors in SQLite; it does not need an API key. OpenRouter at `https://openrouter.ai/api/v1` is the primary composer, trying the two metered routes `nvidia/nemotron-3-nano-30b-a3b` and `qwen/qwen-2.5-7b-instruct`, then the zero-priced `openrouter/free`. The metered tier leads because the account-wide free daily quota returns 429 before any completion exists; the project brief permits the owner's own API keys, and at these token volumes the cost is negligible. Each OpenRouter model gets a 15-second cap. A recognized account-wide free daily quota 429 stops OpenRouter retries and routes directly to OpenCode Zen; other OpenRouter errors exhaust the chain before OpenCode. The OpenCode model chain defaults to Nemotron 3.5 Lightning Free, Big Pickle, and Space Bunny Free, with a 12-second per-model cap. These are currently listed as zero-priced, limited-time routes. Bounded worst case for a full cascade is three OpenRouter routes at 15s plus three OpenCode routes at 12s, or 81 seconds, before RAG/MCP overhead. Because the OpenCode chain and the SQLite templates follow OpenRouter, the service still produces live answers with no credit.

## Stop

Press `Ctrl-C` in the foreground launcher. For a background service, start with `./scripts/start_local.sh --detach` and stop it with `./scripts/stop_local.sh`.
