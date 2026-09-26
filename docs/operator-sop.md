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
./scripts/start_local.sh --no-browser
```

The launcher loads `.env`, starts the API, waits for `/health`, and streams logs. Visit `http://127.0.0.1:8000/` in a browser. Useful runtime endpoints are `/health`, `/health?deep=true`, and `/api/tools`.

Local development uses `MSAIE_MCP_TRANSPORT=inprocess`. Set it to `stdio` to have the official MCP client launch the FastMCP server process. The stdio mode exercises protocol discovery and tool calls; the in-process mode calls the registered tool functions directly.

## Provider configuration

Retrieval uses `sentence-transformers/all-MiniLM-L6-v2` locally and does not need an API key. If using remote answer refinement, set `MSAIE_LLM_BASE_URL`, `MSAIE_LLM_API_KEY`, and `MSAIE_LLM_MODEL`; these variables do not configure embeddings. Optional remote MiniLM serving uses only the separate `MSAIE_EMBEDDING_*` variables in `.env.example`.

## Stop

Press `Ctrl-C` in the foreground launcher. For a background service, start with `./scripts/start_local.sh --detach` and stop it with `./scripts/stop_local.sh`.
