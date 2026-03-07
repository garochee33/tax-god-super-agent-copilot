# Tax God - Railway Deployment Guide

## Quick Start

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init
```

### 2. Add Services

In Railway dashboard, add:
- **PostgreSQL** (from Railway's template)
- **Redis** (from Railway's template)

### 3. Configure Environment Variables

In Railway dashboard → your service → Variables, add:

```
# Required - Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate: openssl rand -hex 32>

# Required - LLM Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Required - Database (auto-populated by Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Required - Redis (auto-populated by Railway Redis)
REDIS_URL=${{Redis.REDIS_URL}}

# Required - Encryption
INTEGRATION_ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# OAuth (optional - for integrations)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://your-app.up.railway.app/api/v1/integrations/callback

QUICKBOOKS_CLIENT_ID=
QUICKBOOKS_CLIENT_SECRET=
QUICKBOOKS_REDIRECT_URI=https://your-app.up.railway.app/api/v1/integrations/callback
```

### 4. Deploy

```bash
# Deploy from CLI
railway up

# Or push to GitHub (auto-deploys if connected)
git push origin main
```

### 5. Run Migrations

Migrations run automatically on deploy via the start command in `railway.json`.

Manual run if needed:
```bash
railway run alembic upgrade head
```

## GitHub Actions Integration

### Add Repository Secrets

In GitHub → Settings → Secrets → Actions:

| Secret | Value |
|--------|-------|
| `RAILWAY_TOKEN` | Get from: `railway whoami --token` |
| `RAILWAY_APP_URL` | Your Railway app URL (e.g., `https://tax-god.up.railway.app`) |

### Workflow

The `.github/workflows/deploy.yml` auto-deploys on push to `main`:
1. Runs CI (lint + test)
2. Deploys to Railway
3. Health check

## Environment Variables Reference

### Required for Production

| Variable | Description | How to Generate |
|----------|-------------|-----------------|
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `INTEGRATION_ENCRYPTION_KEY` | Fernet key for OAuth tokens | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `OPENAI_API_KEY` | OpenAI API key | Get from OpenAI dashboard |
| `ANTHROPIC_API_KEY` | Anthropic API key | Get from Anthropic console |

### Auto-Populated by Railway

| Variable | Source |
|----------|--------|
| `DATABASE_URL` | Railway PostgreSQL service |
| `REDIS_URL` | Railway Redis service |
| `PORT` | Railway runtime |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Logging verbosity |
| `COST_HARD_LIMIT_DAILY` | 200.00 | Daily spend cap |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | JWT expiry |

## Monitoring

### Health Endpoints

- `/health` - Basic health check
- `/health/detailed` - Full system status
- `/readiness` - Kubernetes-style readiness probe
- `/metrics` - Prometheus metrics

### Logs

```bash
railway logs
```

## Troubleshooting

### Database Connection Failed

1. Ensure PostgreSQL service is running
2. Check `DATABASE_URL` is set correctly
3. Run: `railway run alembic upgrade head`

### Redis Connection Failed

1. Ensure Redis service is running
2. Check `REDIS_URL` is set correctly
3. App degrades gracefully without Redis (uses in-memory)

### OAuth Callback Failed

1. Ensure redirect URIs match your Railway URL
2. Update OAuth app settings in Google/QuickBooks console
3. Check `INTEGRATION_ENCRYPTION_KEY` is set

## Cost Optimization

Railway charges by usage. To minimize costs:

1. Use single replica (`numReplicas: 1`)
2. Set reasonable resource limits
3. Enable auto-sleep for development environments
4. Monitor with `/metrics` endpoint
