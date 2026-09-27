# Local Startup and Hosting

## Local workflow

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
MSAIE_MCP_TRANSPORT=stdio ./scripts/start_local.sh --no-browser
```

The local launcher builds the policy index when it is missing and waits for `/health/ready`. Use `/health` for component details, `/api/tools` for available tools, and `./scripts/stop_local.sh` for a detached process.

Before starting the local app, set `MSAIE_LLM_API_KEY` in the ignored local `.env`. The required `https://openrouter.ai/api/v1` endpoint and `openrouter/free` final fallback are prefilled in `.env.example` and enforced by the application. The app tries the pinned Qwen, Nemotron Lightning, and Gemma models first. Verify `/health` reports the provider as configured and `/health/ready` returns `status=ok`. Then confirm an evidence-backed `/chat` response ends with an `llm_refinement` trace event showing the requested/resolved model, attempted model list, and `refinement.status=completed`. Without a successful, validated LLM response, `/chat` returns HTTP 503 rather than presenting the retrieval draft.

## Render hosting, gated by CI

`render.yaml` defines the existing `Project-HR-Agent` service with Python runtime, `/health/ready`, stdio MCP, and `autoDeployTrigger: off`. GitHub Actions runs compileall, full pytest (including real stdio MCP discovery/calls), an explicit MCP smoke command, and the 25-case golden evaluation over both in-process and stdio transports; it uploads both JSON/Markdown report pairs as an artifact. A separate deploy job depends on all those checks and triggers Render for the exact tested SHA. It remains disabled until `RENDER_DEPLOY_ENABLED=true` and `RENDER_DEPLOY_HOOK_URL` are configured in GitHub. Before enabling it, sync the Blueprint or update the existing Render service so its Docker/commit-on-push/no-health-check settings no longer bypass or conflict with this gate. The workflow pins its GitHub-maintained actions to verified release commits and Dependabot checks for updates weekly. It does not need an OpenRouter secret: golden evaluation is orchestrator-level and provider tests use fakes/mocked HTTP. Test the real provider separately with synthetic demo input.

1. Connect this standalone repository to GitHub and the Render web service.
2. Keep the required OpenRouter credential in the Render-managed `MSAIE_LLM_API_KEY` secret; do not commit it. `MSAIE_LLM_BASE_URL=https://openrouter.ai/api/v1` and `MSAIE_LLM_FALLBACK_MODEL=openrouter/free` are set by the Blueprint.
3. Confirm the GitHub Actions check appears on the linked branch. Render must not deploy if checks fail or no check is detected.
4. After deployment, test `/health?deep=true`, both demo tasks, citations, the confirmation boundary, and the reported embedding/MCP configuration.
5. Measure warm task latency and the cold-start/index-build path separately. The `/tmp` index may be rebuilt after a free-tier restart.

The active checkout's `origin` is `https://github.com/MSAIE2027/Project-HR-Agent.git`. The private `MSAIE2027/Project-HR-Agent` repo and linked Render service already exist, but the local source has not been pushed, Render has no deploy history, and its settings do not yet match the Blueprint. The assigned URL is `https://project-hr-agent.onrender.com`; do not treat it as live until a deployment succeeds. See [`deployed.md`](../deployed.md) and the [demo package](../demo/README.md) for remaining hosting steps.
