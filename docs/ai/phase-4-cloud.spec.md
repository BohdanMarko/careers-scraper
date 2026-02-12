# Phase 4: Cloud Deployment

Deploy to Azure with managed infrastructure.

**Prerequisite:** Phase 3 (Production Readiness) must be complete.

---

## Scope

- Provision Azure resources (ACR, ACA, PostgreSQL, Key Vault)
- Configure Azure Key Vault secrets with managed identity
- Deploy to Azure Container Apps
- Verify production: dashboard + scraping + Telegram notifications
- Set up Azure Monitor alerts

## Non-Goals

- No AWS deployment (future consideration after Azure is stable)
- No AI parsing (Phase 5)
- No multi-user support (Phase 5)
- No Application Insights integration (Phase 5)
- No custom domain or SSL certificate management (manual Azure setup)

---

## Technical Design

### 1. Azure Container Apps (ACA)

| Option | Fits This App? | Cost | Complexity |
|--------|---------------|------|------------|
| App Service | Adequate | ~$13/mo (B1) | Low |
| **Container Apps** | **Best fit** | **~$5-15/mo (consumption)** | **Low-Medium** |
| Functions | Poor fit (no Selenium, cold starts) | ~$1-5/mo | High |
| AKS | Massive overkill | ~$70+/mo | Very High |

**Why ACA wins:**
- Consumption-based pricing (idle most of the time, scrapes 1x/hour)
- Single container runs both uvicorn + APScheduler
- Built-in HTTPS/TLS termination
- Min replicas = 1 keeps the scheduler alive

### 2. Selenium: In-Container

Run Chrome in the same container. Adding a separate Selenium Grid adds operational complexity for zero benefit at 3-5 scrapers running once per hour. Container needs ~1 vCPU, 2 GB RAM.

### 3. Azure Resources

| Resource | Tier | Estimated Cost |
|----------|------|---------------|
| Azure Container Registry | Basic | ~$5/mo |
| Azure Container Apps | Consumption plan | ~$5-15/mo |
| Azure Database for PostgreSQL | Flexible Server B1ms (1 vCore, 2 GB RAM) | ~$13/mo |
| Azure Key Vault | Free tier (<10k txn/mo) | $0 |
| Managed Identity | System-assigned | $0 |
| **Total** | | **~$23-33/mo** |

### 4. PostgreSQL Configuration

- **Why PostgreSQL over Azure SQL (MSSQL):** `psycopg2` is pip-installable; MSSQL requires `pyodbc` + ODBC drivers which are painful in Docker containers. PostgreSQL has first-class Python ecosystem support.
- **Tier:** Burstable B1ms (1 vCore, 2 GB RAM)
- **Connection:** `postgresql+psycopg2://user:pass@host:5432/db?sslmode=require`
- Same Alembic migrations as local SQLite -- SQLAlchemy abstracts the differences

### 5. Azure Key Vault Integration

At startup, before `Settings()` instantiation: if `CAREERS_AZURE_KEYVAULT_URL` is set, fetch secrets from Key Vault using `DefaultAzureCredential` and inject as environment variables. The application itself is unaware of Key Vault -- it always reads env vars.

```python
# src/careers_scraper/config.py (Key Vault bootstrap)
def load_keyvault_secrets():
    vault_url = os.environ.get("CAREERS_AZURE_KEYVAULT_URL")
    if not vault_url:
        return
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    secret_mapping = {
        "careers-database-url": "CAREERS_DATABASE_URL",
        "careers-telegram-bot-token": "CAREERS_TELEGRAM_BOT_TOKEN",
        "careers-telegram-chat-id": "CAREERS_TELEGRAM_CHAT_ID",
        "careers-dashboard-api-key": "CAREERS_DASHBOARD_API_KEY",
    }
    for secret_name, env_var in secret_mapping.items():
        if env_var not in os.environ:
            secret = client.get_secret(secret_name)
            os.environ[env_var] = secret.value
```

Settings with `env_prefix="CAREERS_"` means env vars are `CAREERS_DATABASE_URL`, `CAREERS_TELEGRAM_BOT_TOKEN`, etc. This prevents collisions in container environments.

### 6. Deployment Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      - run: |
          az acr build --registry $ACR_NAME --image careers-scraper:${{ github.sha }} .
          az containerapp update --name careers-scraper --resource-group $RG \
            --image $ACR_NAME.azurecr.io/careers-scraper:${{ github.sha }}
```

### 7. Azure Monitor Alerts

Configure alerts for:
- Container restart count > 3 in 10 minutes
- Health check (`/health`) failure
- CPU/memory exceeding 80% sustained

---

## Data Model Changes

None. The same Alembic migrations run against PostgreSQL as against SQLite.

---

## API Changes

None. Same endpoints, same behavior. Only the infrastructure changes.

---

## Configuration Changes

| Setting | Value (Azure) |
|---------|--------------|
| `CAREERS_DATABASE_URL` | `postgresql+psycopg2://...?sslmode=require` (from Key Vault) |
| `CAREERS_TELEGRAM_BOT_TOKEN` | From Key Vault |
| `CAREERS_TELEGRAM_CHAT_ID` | From Key Vault |
| `CAREERS_DASHBOARD_API_KEY` | From Key Vault |
| `CAREERS_AZURE_KEYVAULT_URL` | Set as ACA env var |
| `CAREERS_ENVIRONMENT` | `production` |

---

## New Files

| File | Purpose |
|------|---------|
| `.github/workflows/deploy.yml` | Azure deployment pipeline |
| `infra/` (optional) | Azure CLI or Bicep scripts for resource provisioning |

---

## New Dependencies

| Package | Purpose |
|---------|---------|
| `azure-identity` | `DefaultAzureCredential` for managed identity |
| `azure-keyvault-secrets` | Fetch secrets from Key Vault |

These are production-only dependencies. Add as optional: `[azure]` group in `pyproject.toml`.

---

## Implementation Checklist

- [ ] Add `azure-identity` and `azure-keyvault-secrets` as optional `[azure]` dependencies
- [ ] Implement Key Vault bootstrap in `config.py`
- [ ] Provision Azure Container Registry (Basic tier)
- [ ] Provision Azure Database for PostgreSQL Flexible Server (B1ms)
- [ ] Run `alembic upgrade head` against Azure PostgreSQL
- [ ] Provision Azure Key Vault and store secrets
- [ ] Create Azure Container App with managed identity
- [ ] Grant Container App identity access to Key Vault and ACR
- [ ] Build and push Docker image to ACR
- [ ] Deploy to Azure Container Apps
- [ ] Verify dashboard loads via Azure URL
- [ ] Verify scraping runs on schedule
- [ ] Verify Telegram notifications arrive
- [ ] Configure Azure Monitor alerts
- [ ] Create `.github/workflows/deploy.yml`
- [ ] Document Azure resource provisioning steps (in `infra/README.md` or similar)

---

## Acceptance Criteria

1. Azure URL loads the dashboard with API key authentication
2. Scraping runs automatically on schedule (APScheduler in-container)
3. Telegram notifications arrive for matching jobs
4. Key Vault secrets resolve correctly via managed identity
5. `alembic upgrade head` works against Azure PostgreSQL
6. Azure Monitor alerts fire on simulated failure
7. Deployment pipeline pushes new image and updates container on `main` branch push

---

## Implementation Notes

- **AWS future compatibility:** The application code is cloud-agnostic. Only the Key Vault bootstrap and infrastructure provisioning are Azure-specific. For AWS: replace Key Vault with AWS Secrets Manager, ACA with ECS Fargate, Azure PostgreSQL with RDS PostgreSQL.
- Set min replicas = 1 on Azure Container Apps to keep the scheduler alive (consumption plan scales to zero by default)
- PostgreSQL connection string must include `?sslmode=require` for Azure
- Use system-assigned managed identity (simpler than user-assigned for a single app)
