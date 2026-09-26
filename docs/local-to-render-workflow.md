# Local Startup and Optional Hosting

## Local workflow

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
./scripts/start_local.sh --no-browser
```

The local launcher builds the policy index when it is missing. Check the returned status at `/health` and available tools at `/api/tools`. Use `./scripts/stop_local.sh` for a detached process.

## Optional hosting

`render.yaml` contains a Python web-service configuration. Set any provider credentials in the hosting dashboard, then connect this standalone repository and select the `main` branch. Keep secrets out of the repository. The app exposes `/health` as its health-check path.
