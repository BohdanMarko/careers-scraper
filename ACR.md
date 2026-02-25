# Plan: Switch from ghcr.io to Azure Container Registry (ACR)

## Why

All job failures are image pull failures from `ghcr.io`. The 3 failed executions had no app logs at all — the container never started. Azure system logs confirm:

```
13:00:01  AssigningReplica — scheduled to a node
13:00:20  PullingImage     — started pulling from ghcr.io
          ... nothing ...
13:10:02  DeadlineExceeded — FAILED
```

Image pull times from ghcr.io are wildly variable: 9s–126s on successful runs, infinite hang on failures. ACR lives in the **same West Europe datacenter** as the Container Apps environment — pulls go over Azure's internal network, consistently under 5s, never flaky.

## Cost

**ACR Basic tier: ~$5/month** (West Europe)
- 10 GB storage included — we use ~0.3 GB (one 329 MB image)
- No per-pull charges
- No egress charges within the same Azure region

Source: https://azure.microsoft.com/en-us/pricing/details/container-registry/

## Image Size (side goal)

Current image is 329 MB. Switching to Alpine base could cut it to ~175–200 MB (-40%):

```dockerfile
FROM python:3.13-alpine
RUN apk add --no-cache chromium chromium-chromedriver
ENV CHROME_BINARY=/usr/bin/chromium-browser
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

Risk: Alpine uses musl libc instead of glibc — needs a test build to confirm Selenium/Chromium work correctly. If `python main.py` completes successfully, it's good to ship.

## Implementation Plan

### Step 1 — One-time manual setup (run once via az CLI)

```bash
# Create ACR in same region as the container app environment
az acr create \
  --name careersscraperacr \
  --resource-group careers-scraper-rg \
  --sku Basic \
  --location westeurope

# Enable system-assigned managed identity on the container app job
az containerapp job identity assign \
  --name careers-scraper-job \
  --resource-group careers-scraper-rg \
  --system-assigned
# → note the principalId in the output

# Grant the job's identity AcrPull (replace <principal-id> from above)
az role assignment create \
  --role AcrPull \
  --assignee <principal-id> \
  --scope $(az acr show --name careersscraperacr --resource-group careers-scraper-rg --query id -o tsv)

# Grant the GitHub Actions service principal AcrPush
# (same service principal used for OIDC in deploy.yml — find its object ID in Azure AD)
az role assignment create \
  --role AcrPush \
  --assignee <github-actions-service-principal-object-id> \
  --scope $(az acr show --name careersscraperacr --resource-group careers-scraper-rg --query id -o tsv)
```

### Step 2 — deploy.yml changes

| What | Current | Proposed |
|------|---------|----------|
| Registry login | `docker/login-action` with `GITHUB_TOKEN` for ghcr.io | `az acr login --name careersscraperacr` (reuses existing OIDC login — no extra step) |
| Image name | `ghcr.io/bohdanmarko/careers-scraper` | `careersscraperacr.azurecr.io/careers-scraper` |
| `packages: write` permission | required | remove (no longer needed) |
| `containerapp job update` flags | `--image ghcr.io/...` | `--image careersscraperacr.azurecr.io/... --registry-server careersscraperacr.azurecr.io --registry-identity system` |

The existing `azure/login@v2` OIDC step already authenticates to Azure before the build — `az acr login` reuses that session, so no new secrets are needed in GitHub.

### Step 3 — Remove ghcr.io registry secret from the job

Currently the job has a `ghcrio-bohdanmarko` secret (PAT). With managed identity pulling from ACR, no registry credentials are needed. After deploy.yml is updated and the job is running from ACR:

```bash
# Remove the old ghcr.io registry config and secret from the job
az containerapp job secret remove \
  --name careers-scraper-job \
  --resource-group careers-scraper-rg \
  --secret-names ghcrio-bohdanmarko
```

## What does NOT change

- Dockerfile (except optionally: base image for size reduction)
- Python code, scraper logic, config
- Telegram secrets (already stored correctly as separate secrets)
- Azure Container Apps Job CRON schedule, timeout, resource allocation
