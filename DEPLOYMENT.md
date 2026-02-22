# Azure Deployment Guide — careers-scraper

## Architecture Overview

```
Azure CRON (every 60 min)
    └── Container Apps Job triggers
            └── Fresh container spins up
                    └── python main.py --single-run (~30–70s)
                            └── Scrape jobs → send Telegram notifications
                                    └── Container exits, Azure tears it down
```

**Why Container Apps Jobs (Consumption plan):**
- No infrastructure running between cycles → ~$0/month compute
- Image hosted on GitHub Container Registry (ghcr.io) → **$0/month total**

---

## Where to Run Commands

This guide uses two environments. Check this table before each step:

| Environment | What runs there | How to open |
|---|---|---|
| **Azure Cloud Shell** | All `az` commands | [portal.azure.com](https://portal.azure.com) → Cloud Shell icon, or [shell.azure.com](https://shell.azure.com) |
| **Local machine** | `docker login`, `docker build`, `docker push` | your normal terminal in the project root |

> **Cloud Shell is pre-authenticated** — no `az login` needed.
> Variables set in Cloud Shell are session-scoped and lost when the session ends.
> Re-run Step 1 at the start of each new Cloud Shell session.

---

## Secret Management Strategy

### How secrets flow in this app

```
Azure Container Apps Job secrets (encrypted at rest)
    └── Injected as environment variables at container startup
            └── config.py reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars
                    └── Falls back to config.yaml values if env vars are absent
```

**What's baked into the Docker image (NOT secret):**
- `config.example.yaml` copied as `config.yaml` — contains vacancies, keywords, and container-appropriate defaults:
  - `environment: production`
  - `dedup_seen_urls: false` — containers are ephemeral; deduplication state does not persist across runs

**What's injected at runtime (secrets):**
- `TELEGRAM_BOT_TOKEN` — your bot token from @BotFather
- `TELEGRAM_CHAT_ID` — your target chat/channel ID

### Option A: Container Apps Job Secrets (used in this guide)

Secrets are stored encrypted in the Container Apps Job definition. They are exposed
to the container as environment variables via `secretref:`. This is the approach
documented throughout this guide.

- No extra Azure services required
- Secrets visible to anyone with Contributor access to the resource group
- Suitable for personal projects and small teams

### Option B: Azure Key Vault + Managed Identity (enterprise-grade)

For stricter access control, store secrets in Key Vault and grant the job a
managed identity to read them. See Appendix A at the bottom of this guide.

---

## Prerequisites

### 1. Open Azure Cloud Shell

Go to [shell.azure.com](https://shell.azure.com) or click the Cloud Shell icon in the Azure Portal toolbar.

- Select **Bash** (not PowerShell) on first launch
- Cloud Shell is already authenticated — no `az login` needed
- First time: it prompts to create a storage account for persistent files — accept it

### 2. Install the Container Apps extension (in Cloud Shell)

```bash
az extension add --name containerapp --upgrade
```

### 3. Install Docker Desktop (locally)

Building the image locally requires Docker Desktop to be installed and running.

- Download from https://www.docker.com/products/docker-desktop/
- **Windows 10 Home:** Docker Desktop requires WSL2. Enable it first:
  ```powershell
  wsl --install
  ```
  Then restart and install Docker Desktop.

Verify Docker is running:
```bash
docker --version
# Should show Docker version 24.x or higher
```

### 4. Gather your Telegram credentials

You need two values before starting:
- **Bot token**: get from @BotFather on Telegram (`/newbot` command)
- **Chat ID**: the numeric ID of the chat/channel that should receive notifications

To find your chat ID:
1. Add your bot to the target chat
2. Send a message to the chat
3. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser
4. Look for `"chat":{"id": -123456789}` — that number is your chat ID

---

## Step 1 — Define Variables

In Azure Cloud Shell, set these variables once. All subsequent `az` commands reference
them so you don't retype names.

```bash
# --- Customize these ---
RESOURCE_GROUP="careers-scraper-rg"
LOCATION="westeurope"              # az account list-locations -o table to see options
GITHUB_USER="your-github-username"
GITHUB_PAT="ghp_xxxxxxxxxxxxxxxxxxxx"   # created in Step 3
GITHUB_IMAGE="ghcr.io/$GITHUB_USER/careers-scraper:latest"
ENVIRONMENT_NAME="careers-scraper-env"
JOB_NAME="careers-scraper-job"
TELEGRAM_TOKEN="REPLACE_WITH_YOUR_BOT_TOKEN"
TELEGRAM_CHAT="REPLACE_WITH_YOUR_CHAT_ID"
```

> **Variables are session-scoped** — re-run this block at the start of each new Cloud Shell session.

---

## Step 2 — Create Resource Group

A resource group is a logical container for all Azure resources in this project.

```bash
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

Expected output: JSON with `"provisioningState": "Succeeded"`

---

## Step 3 — Create GitHub Personal Access Token

A PAT lets you push images to GitHub Container Registry and lets Azure pull them.

### Create the PAT

1. Go to **GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name (e.g. `careers-scraper-ghcr`)
4. Select scope: **`write:packages`** (automatically includes `read:packages`)
5. Click **Generate token** and copy it immediately — GitHub shows it only once

### Set the variable

In **Azure Cloud Shell** (if not already set from Step 1):
```bash
GITHUB_PAT="ghp_..."   # paste your token here
```

### Log in to ghcr.io

**[Local machine]** — run this in your local terminal where Docker Desktop is installed:

```bash
# Set these locally if your local shell session doesn't already have them
GITHUB_USER="your-github-username"
GITHUB_PAT="ghp_..."

echo $GITHUB_PAT | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

Expected output: `Login Succeeded`

> **Note:** Docker Desktop must be installed and running before this step.
> On Windows 10 Home, Docker requires WSL2 (see Prerequisites).

---

## Step 4 — Build and Push the Docker Image

### What the Dockerfile does

```dockerfile
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BINARY=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src/ src/

COPY config.example.yaml config.yaml

CMD ["python", "main.py", "--single-run"]
```

Key points:
- `chromium` and `chromium-driver` are installed via `apt` — no webdriver-manager needed
- `CHROME_BINARY` and `CHROMEDRIVER_PATH` env vars tell the scrapers where to find them
- `config.example.yaml` is baked in as `config.yaml` — contains only vacancies/keywords, no secrets

### Build and push

**Run on your local machine** (from the project root `D:\Projects\careers-scraper`):

```bash
# Set these locally if your local shell session doesn't already have them
GITHUB_USER="your-github-username"
GITHUB_IMAGE="ghcr.io/$GITHUB_USER/careers-scraper:latest"

docker build -t $GITHUB_IMAGE .
docker push $GITHUB_IMAGE
```

The first build takes 3–8 minutes (downloads the Chromium layer). Subsequent builds
are faster because Docker caches unchanged layers.

To verify the image was pushed, visit:
`https://github.com/$GITHUB_USER?tab=packages`

---

## Step 5 — Create Container Apps Environment

**Run in Azure Cloud Shell** — all remaining `az` commands in Steps 5–9 run in Cloud Shell.

The environment is a shared networking boundary for Container Apps and Jobs.
The Consumption plan has no base fee.

```bash
az containerapp env create \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION
```

This takes ~2 minutes.

---

## Step 6 — Create the Scheduled Job

This is the main step. It creates a CRON-triggered job that runs every 60 minutes.
Telegram secrets are stored as Container Apps secrets and injected as env vars.

```bash
az containerapp job create \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --trigger-type Schedule \
  --cron-expression "0 * * * *" \
  --image $GITHUB_IMAGE \
  --registry-server "ghcr.io" \
  --registry-username $GITHUB_USER \
  --registry-password $GITHUB_PAT \
  --cpu 0.5 \
  --memory 1.0Gi \
  --replica-timeout 300 \
  --replica-retry-limit 1 \
  --secrets \
      telegram-bot-token="$TELEGRAM_TOKEN" \
      telegram-chat-id="$TELEGRAM_CHAT" \
  --env-vars \
      TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
      TELEGRAM_CHAT_ID=secretref:telegram-chat-id
```

**What each flag does:**

| Flag | Value | Purpose |
|------|-------|---------|
| `--trigger-type Schedule` | Schedule | CRON-based trigger |
| `--cron-expression "0 * * * *"` | every hour | Standard cron syntax (minute hour day month weekday) |
| `--cpu 0.5` | 0.5 vCPU | Enough for Selenium + Chromium |
| `--memory 1.0Gi` | 1 GB | Chromium needs ~300–500 MB |
| `--replica-timeout 300` | 5 minutes | Kill the job if it hangs |
| `--replica-retry-limit 1` | 1 retry | Retry once on failure |
| `--secrets` | key=value pairs | Stored encrypted in Azure, never in image |
| `--env-vars ... secretref:` | references | Tells Azure to inject the secret as an env var |

---

## Step 7 — Trigger a Manual Test Run

Don't wait 60 minutes — trigger the job immediately to verify it works:

```bash
az containerapp job start \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP
```

Check the execution status (run a few times over 2 minutes):

```bash
az containerapp job execution list \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

Expected output:

```
Name                          StartTime                     Status
----------------------------  ----------------------------  ---------
careers-scraper-job-abc123    2024-01-15T10:00:00Z          Succeeded
```

If status is `Failed`, check logs (see Step 8).

---

## Step 8 — View Logs

### Stream logs from the latest execution

```bash
az containerapp logs show \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --type console \
  --execution-name $(az containerapp job execution list --name $JOB_NAME --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
```

### Query logs via Log Analytics (after a few minutes delay)

First find your Log Analytics workspace:
```bash
az containerapp env show \
  --name $ENVIRONMENT_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.appLogsConfiguration.logAnalyticsConfiguration.customerId" \
  -o tsv
```

Then query in the Azure Portal:
1. Go to Azure Portal → Container Apps Environment → Logs
2. Run this KQL query:
```kql
ContainerAppConsoleLogs_CL
| where ContainerJobName_s == "careers-scraper-job"
| order by TimeGenerated desc
| project TimeGenerated, Log_s
| limit 100
```

---

## Step 9 — Verify Telegram Notification

After a successful run, you should receive a message in your Telegram chat listing
any jobs that matched your configured keywords.

If no message arrives:
1. Check execution status is `Succeeded` (not `Failed`)
2. Check logs for errors: `"Error scraping"` or `"Failed to send"`
3. Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` were set correctly
4. Confirm the bot has been added to the target chat with permission to send messages

---

## Updating After Code Changes

When you modify scraper logic, keywords in `config.example.yaml`, or any source file:

**On your local machine** — rebuild and push the new image:
```bash
docker build -t $GITHUB_IMAGE .
docker push $GITHUB_IMAGE
```

**In Azure Cloud Shell** — update the job and trigger a test run:
```bash
# Set GITHUB_IMAGE in Cloud Shell if not already set from Step 1
GITHUB_IMAGE="ghcr.io/$GITHUB_USER/careers-scraper:latest"

az containerapp job update \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $GITHUB_IMAGE

az containerapp job start --name $JOB_NAME --resource-group $RESOURCE_GROUP
```

---

## Updating Telegram Secrets

If you rotate your bot token or change the chat ID:

```bash
az containerapp job secret set \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --secrets \
      telegram-bot-token="NEW_TOKEN_HERE" \
      telegram-chat-id="NEW_CHAT_ID_HERE"
```

The change takes effect on the next job execution (no restart needed).

---

## Changing the CRON Schedule

```bash
# Every 30 minutes
az containerapp job update \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --cron-expression "*/30 * * * *"

# Every 2 hours, only on weekdays
az containerapp job update \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --cron-expression "0 */2 * * 1-5"
```

---

## Cost Breakdown

| Resource | Monthly cost |
|----------|-------------|
| Container Apps Environment (Consumption) | $0 — no base fee |
| vCPU-seconds (1 run/hr × 70s × 0.5 vCPU × 744 hrs = 26,040) | $0 — free tier is 180,000 |
| GB-seconds (1 run/hr × 70s × 1 GB × 744 hrs = 52,080) | $0 — free tier is 360,000 |
| GitHub Container Registry | $0 — free for public packages, free tier for private |
| **Total** | **$0/month** |

---

## Teardown (Delete Everything)

```bash
az group delete --name $RESOURCE_GROUP --yes --no-wait
```

This deletes the resource group and everything inside it (environment, job).

---

## Troubleshooting

### Job status is `Failed`

Check logs first:
```bash
az containerapp logs show \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --type console \
  --execution-name $(az containerapp job execution list --name $JOB_NAME --resource-group $RESOURCE_GROUP --query "[0].name" -o tsv)
```

Common causes:
- **`chromium: not found`** — Chromium not installed in the image. Verify the `RUN apt-get install chromium chromium-driver` step in the Dockerfile ran successfully during `docker build`.
- **`ModuleNotFoundError`** — `pip install` failed during build. Check `docker build` output.
- **`FileNotFoundError: config.yaml`** — The `COPY config.example.yaml config.yaml` step failed.
- **`Telegram send failed`** — Wrong token or chat ID. Check secrets with the command below.

### Verify secrets are set

```bash
az containerapp job secret list \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

This shows secret names (not values). Confirms they exist.

### Job never triggers

```bash
az containerapp job show \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.scheduleTriggerConfig"
```

Verify the CRON expression is correct. Use https://crontab.guru to validate.

### Image pull fails

```bash
az containerapp job show \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.configuration.registries"
```

Ensure `server` is `ghcr.io` and `username` matches your GitHub username. Re-run the
`job update` with fresh credentials if your PAT has expired.

---

## Appendix A — Azure Key Vault + Managed Identity (Optional)

Use this if you want stricter access control: secrets are stored in Key Vault and
only the job's managed identity can read them (not any Contributor on the resource group).

```bash
KEYVAULT_NAME="careers-scraper-kv"   # globally unique
IDENTITY_NAME="careers-scraper-id"

# 1. Create Key Vault
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 2. Store secrets in Key Vault
az keyvault secret set --vault-name $KEYVAULT_NAME --name "telegram-bot-token" --value "$TELEGRAM_TOKEN"
az keyvault secret set --vault-name $KEYVAULT_NAME --name "telegram-chat-id"   --value "$TELEGRAM_CHAT"

# 3. Create a User-Assigned Managed Identity
az identity create \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

IDENTITY_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
IDENTITY_PRINCIPAL=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
KEYVAULT_ID=$(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

# 4. Grant the identity read access to Key Vault secrets
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee $IDENTITY_PRINCIPAL \
  --scope $KEYVAULT_ID

# 5. Get Key Vault secret URIs
TOKEN_URI=$(az keyvault secret show --vault-name $KEYVAULT_NAME --name telegram-bot-token --query id -o tsv)
CHAT_URI=$(az keyvault secret show  --vault-name $KEYVAULT_NAME --name telegram-chat-id   --query id -o tsv)

# 6. Create the job with Key Vault references
az containerapp job create \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --trigger-type Schedule \
  --cron-expression "0 * * * *" \
  --image $GITHUB_IMAGE \
  --registry-server "ghcr.io" \
  --registry-username $GITHUB_USER \
  --registry-password $GITHUB_PAT \
  --cpu 0.5 --memory 1.0Gi \
  --replica-timeout 300 \
  --replica-retry-limit 1 \
  --mi-user-assigned $IDENTITY_ID \
  --secrets \
      telegram-bot-token="keyvaultref:$TOKEN_URI,identityref:$IDENTITY_ID" \
      telegram-chat-id="keyvaultref:$CHAT_URI,identityref:$IDENTITY_ID" \
  --env-vars \
      TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
      TELEGRAM_CHAT_ID=secretref:telegram-chat-id
```

To rotate a secret: update it in Key Vault only (`az keyvault secret set ...`).
The job automatically picks up the new value on the next run.

---

## Appendix B — Azure Container Registry (Alternative, ~$5/month)

Use ACR instead of ghcr.io if you prefer cloud-side image builds — no Docker Desktop
needed on your machine. Images are built directly in Azure using `az acr build`.

**Trade-off:** ACR Basic costs ~$5/month; ghcr.io is free.

### Setup

```bash
ACR_NAME="careersscraperacr"   # globally unique, lowercase, 5–50 chars, no hyphens

# 1. Create the registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# 2. Build and push — runs in the cloud, no Docker Desktop required
az acr build \
  --registry $ACR_NAME \
  --image careers-scraper:latest \
  .

# 3. Retrieve credentials for Container Apps
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USER=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASS=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# 4. Create the job using ACR image
az containerapp job create \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENVIRONMENT_NAME \
  --trigger-type Schedule \
  --cron-expression "0 * * * *" \
  --image "$ACR_SERVER/careers-scraper:latest" \
  --registry-server $ACR_SERVER \
  --registry-username $ACR_USER \
  --registry-password $ACR_PASS \
  --cpu 0.5 --memory 1.0Gi \
  --replica-timeout 300 \
  --replica-retry-limit 1 \
  --secrets \
      telegram-bot-token="$TELEGRAM_TOKEN" \
      telegram-chat-id="$TELEGRAM_CHAT" \
  --env-vars \
      TELEGRAM_BOT_TOKEN=secretref:telegram-bot-token \
      TELEGRAM_CHAT_ID=secretref:telegram-chat-id
```

### Updating after code changes (ACR)

```bash
az acr build --registry $ACR_NAME --image careers-scraper:latest .

az containerapp job update \
  --name $JOB_NAME \
  --resource-group $RESOURCE_GROUP \
  --image "$ACR_SERVER/careers-scraper:latest"

az containerapp job start --name $JOB_NAME --resource-group $RESOURCE_GROUP
```
