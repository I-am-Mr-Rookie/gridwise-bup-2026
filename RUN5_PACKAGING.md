# Run 5 Packaging Preparation

Prepared on 2026-09-18. **Nothing below has been executed.** Local Docker is not usable and must not be run or troubleshot on this device. In Run 8, the authenticated Railway Codex integration will perform the remote Dockerfile build and deployment. Registry publication still requires separate authorization.

## Startup contract

- Image: `python:3.11-slim`.
- Process: `uvicorn app.main:app` bound to `0.0.0.0`.
- Port: shell-expanded `${PORT:-8000}`. The Dockerfile intentionally uses `sh -c`; a direct JSON/exec-form command would not expand `$PORT`. `exec` then makes Uvicorn the container process.
- Required secret: `MERGE_API_KEY`. Optional configuration already has application defaults: `MERGE_BASE_URL`, `LLM_MODEL`, and `LLM_REASONING_EFFORT`.
- Build context excludes environment files, Git/Railway metadata, virtual environments, caches, tests, logs, and Markdown evidence. The image copies only `requirements.txt` and `app/`.

## Run 8: Railway-only container build and deployment

Use the authenticated Railway Codex integration; do not run local Docker or troubleshoot the local daemon. Confirm the connected project/service in the integration before changing remote state. Railway automatically detects the root `Dockerfile`; set `MERGE_API_KEY` as a Railway secret and the three nonsecret runtime variables to the values below without printing the secret.

```powershell
$project = '<railway-project-id-or-name>'
$service = '<railway-service-id-or-name>'
$environment = 'production'

railway link --project $project --environment $environment --service $service
$env:MERGE_API_KEY | railway variable set MERGE_API_KEY --stdin --service $service --environment $environment --skip-deploys
railway variable set MERGE_BASE_URL=https://api-gateway.merge.dev/v1/openai LLM_MODEL=gpt-5.6-luna LLM_REASONING_EFFORT=high --service $service --environment $environment --skip-deploys
railway up --service $service --environment $environment
railway domain --service $service --environment $environment
```

The CLI block is a command-level reference only; prefer the authenticated integration in Run 8. Then use the generated HTTPS URL for `/health` and the all-10 external HTTP runner. A deployment alone does not prove a public domain or healthy runtime.

## Run 8: registry fallback (separately gated)

Only after explicit registry-publication authorization, use a remote/hosted build path rather than local Docker. Record an exact pullable tag and digest only after remote push, clean pull/run verification, health, and one real optimization request succeed. Railway deployment evidence alone does not prove that a separately pullable registry image exists.
