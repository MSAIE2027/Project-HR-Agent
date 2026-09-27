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

`render.yaml` defines the existing `Project-HR-Agent` service with Python runtime, `/health/ready`, stdio MCP, and `autoDeployTrigger: off`. Its build installs `requirements-render.txt`, which uses the same pinned Hugging Face MiniLM INT8 ONNX Runtime path as the application, then compiles the app and builds the dense SQLite vector index at `.data/rag_index.sqlite3`. Both Render and GitHub Actions call `scripts/verify_pinned_index.py` to check the exact model, revision, ONNX backend, 256-token truncation, 384 dimensions, and 120/20 chunks. Public readiness applies the same baseline check and rejects a sparse fallback. GitHub Actions also runs full pytest (including real stdio MCP discovery/calls), an explicit MCP smoke command, and the 30-case golden evaluation over both in-process and stdio transports; it uploads both JSON/Markdown report pairs as an artifact. A separate deploy job depends on all those checks and triggers Render for the exact tested SHA. It remains disabled until `RENDER_DEPLOY_ENABLED=true` and `RENDER_DEPLOY_HOOK_URL` are configured in GitHub. Render auto-deploy remains off. The workflow pins its GitHub-maintained actions to verified release commits and Dependabot checks for updates weekly. It does not need an OpenRouter secret: golden evaluation is orchestrator-level and provider tests use fakes/mocked HTTP. Test the real provider separately with synthetic demo input.

1. Connect this standalone repository to GitHub and the Render web service.
2. Keep the OpenRouter credential in Render's environment variables; never commit or print it. The app accepts the existing `OPENROUTER_API_KEY` alias, while `MSAIE_LLM_BASE_URL=https://openrouter.ai/api/v1` and `MSAIE_LLM_FALLBACK_MODEL=openrouter/free` come from the Blueprint.
3. Wait for the full GitHub Actions run on the deployment commit to pass, then deploy that tested SHA in Render. Auto-deploy remains off.
4. After deployment, test `/health/ready`, `/health?deep=true`, both demo tasks, citations, the confirmation boundary, and the reported Hugging Face dense embedding/MCP configuration. The synthetic hosted checks are available with `python scripts/smoke_hosted_demo.py` after OpenRouter capacity is available.
5. Measure warm task latency and free-tier cold starts separately. The policy SQLite index is generated during each build into the deployed app's `.data` directory.

The current service and release state, including any live provider or recording gate, is maintained in [`../deployed.md`](../deployed.md). Sanitized hosted request evidence is in [`../evidence/hosted-pto-smoke.md`](../evidence/hosted-pto-smoke.md); the presenter checklist is in the [demo package](../demo/README.md).
