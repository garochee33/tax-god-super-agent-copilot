# 🐳 Tax God - Local Docker Deployment Guide

**Complete local development environment using Docker Compose**

---

## 🚀 Quick Start (3 Steps)

### Step 1: Prerequisites
```bash
# Install Docker & Docker Compose
# macOS: brew install docker docker-compose
# Linux: sudo apt install docker.io docker-compose
# Windows: Install Docker Desktop
```

### Step 2: Environment Setup
```bash
# Clone or navigate to project
cd tax-god-copilot

# Create environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
# Add: OPENAI_API_KEY=sk-your-key
# Add: ANTHROPIC_API_KEY=sk-ant-your-key
```

### Step 3: Launch Tax God
```bash
# Build and start all services
docker-compose up -d --build

# Check services are running
docker-compose ps
```

**That's it! Tax God is now running locally.** 🎉

---

## 📊 Service Architecture

```
Tax God Local Stack
├── 🌐 API Server (FastAPI)     → http://localhost:8000
├── 🗄️ PostgreSQL Database      → localhost:5432
├── 🔴 Redis Cache              → localhost:6379
├── 🐰 RabbitMQ Message Queue   → localhost:5672 (web:15672)
├── 📊 Prometheus Monitoring    → http://localhost:9090
├── 📈 Grafana Dashboard        → http://localhost:3000 (admin/admin)
├── 🌸 Flower Task Monitor      → http://localhost:5555
└── 🔧 Celery Workers           → Background processing
```

---

## 🌐 Access Points

| Service | URL | Purpose | Credentials |
|---------|-----|---------|-------------|
| **Tax God API** | http://localhost:8000 | Main application | - |
| **API Docs** | http://localhost:8000/api/docs | Interactive API docs | - |
| **Health Check** | http://localhost:8000/health | System health | - |
| **Grafana** | http://localhost:3000 | Monitoring dashboard | admin/admin |
| **Prometheus** | http://localhost:9090 | Metrics collection | - |
| **Flower** | http://localhost:5555 | Celery task monitoring | - |
| **RabbitMQ** | http://localhost:15672 | Message queue admin | guest/guest |
| **PostgreSQL** | localhost:5432 | Database | taxgod/taxgod123 |
| **Redis** | localhost:6379 | Cache | - |

---

## 🧪 Testing Tax God

### Basic Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "3.0.0", ...}
```

### Test Advanced Tax Processing
```bash
curl -X POST http://localhost:8000/api/v1/advanced/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can I deduct home office expenses?",
    "clientId": "test_client_123",
    "requireCitations": true
  }'
```

### Test Task Decomposition
```bash
curl -X POST http://localhost:8000/api/v1/advanced/decompose \
  -H "Content-Type: application/json" \
  -d '{"query": "Complex multi-state tax filing assistance"}'
```

### Test Memory Retrieval
```bash
curl -X POST http://localhost:8000/api/v1/advanced/memory \
  -H "Content-Type: application/json" \
  -d '{"query": "tax deductions", "clientId": "test_client"}'
```

---

## 📊 Monitoring & Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### Database Access
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U taxgod -d taxgod

# Or use any PostgreSQL client:
# Host: localhost:5432
# Database: taxgod
# User: taxgod
# Password: taxgod123
```

### Redis Access
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Or use any Redis client:
# Host: localhost:6379
```

---

## 🔧 Development Workflow

### Code Changes
```bash
# Edit code locally
nano app/services/advanced_orchestrator.py

# Rebuild and restart
docker-compose up -d --build api
```

### Run Tests
```bash
# Run comprehensive test suite (46 tests)
docker-compose exec api pytest tests/ -v

# Run algorithm tests
docker-compose exec api python3 test_algorithms.py

# Run Trinity integration tests
docker-compose exec api python3 test_trinity_integration.py
```

### Database Migrations
```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Add new feature"

# Apply migrations
docker-compose exec api alembic upgrade head
```

---

## 🎛️ Service Management

### Start Services
```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api
docker-compose up -d postgres redis
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ destroys data)
docker-compose down -v
```

### Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart celery-worker
```

### View Resource Usage
```bash
# Container resource usage
docker stats

# Disk usage
docker system df
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here
APP_VERSION=3.0.0

# Database (Docker internal networking)
DATABASE_URL=postgresql+asyncpg://taxgod:taxgod123@postgres:5432/taxgod
REDIS_URL=redis://redis:6379/0

# Celery (background tasks)
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
CELERY_RESULT_BACKEND=redis://redis:6379/1

# AI API Keys (REQUIRED)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Integrations (Optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
QUICKBOOKS_CLIENT_ID=your-quickbooks-client-id
QUICKBOOKS_CLIENT_SECRET=your-quickbooks-secret

# Cost Governance
COST_SOFT_LIMIT_PER_QUERY=0.50
COST_SOFT_LIMIT_PER_CLIENT_MONTH=100.00
COST_HARD_LIMIT_DAILY=200.00
```

### Docker Compose Overrides
Create `docker-compose.override.yml` for local customizations:
```yaml
version: "3.9"
services:
  api:
    environment:
      DEBUG: true
    volumes:
      - ./app:/app/app  # Mount local code for hot reload
      - ./specs:/app/specs
```

---

## 🐛 Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
# ports: ["8001:8000"]
```

**Database connection failed:**
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

**API returns errors:**
```bash
# Check API logs
docker-compose logs api

# Test basic connectivity
curl http://localhost:8000/health

# Check if services are healthy
docker-compose ps
```

### Performance Tuning

**Increase memory limits:**
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

**Scale workers:**
```bash
# Add more Celery workers
docker-compose up -d --scale celery-worker=3
```

---

## 🔄 Data Management

### Backup Database
```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U taxgod taxgod > taxgod_backup.sql

# Backup Redis
docker-compose exec redis redis-cli --rdb /tmp/redis_backup.rdb
```

### Restore Database
```bash
# Restore PostgreSQL
docker-compose exec -T postgres psql -U taxgod taxgod < taxgod_backup.sql
```

### Reset Everything
```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v --remove-orphans

# Remove all images
docker-compose down --rmi all

# Clean rebuild
docker-compose up -d --build --force-recreate
```

---

## 🚀 Scaling Up

### To Cloud Deployment
Once tested locally, deploy to cloud:

```bash
# AWS ECS
aws ecs create-cluster --cluster-name tax-god-cluster
aws ecs create-service --cluster tax-god-cluster --service-name tax-god-service --task-definition tax-god-task

# Or use Docker Compose in cloud
# Just change environment variables for cloud services
```

### To Kubernetes
```bash
# Convert docker-compose to Kubernetes
kompose convert -f docker-compose.yml

# Deploy to Kubernetes cluster
kubectl apply -f tax-god-k8s/
```

### To Replit
```bash
# Follow REPLIT_AGENT_README.md
python3 scripts/setup_replit_agent.py
./start_replit.sh
```

---

## 📋 Service Status Check

Run this to verify everything is working:

```bash
#!/bin/bash
echo "🔍 Tax God Local Stack Health Check"
echo "==================================="

# Check containers
echo "🐳 Container Status:"
docker-compose ps

echo ""
echo "🌐 Service Health:"

# API Health
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Tax God API: Running"
else
    echo "❌ Tax God API: Failed"
fi

# Database
if docker-compose exec -T postgres pg_isready -U taxgod -d taxgod > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Running"
else
    echo "❌ PostgreSQL: Failed"
fi

# Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Failed"
fi

# RabbitMQ
if curl -s http://guest:guest@localhost:15672/api/overview > /dev/null; then
    echo "✅ RabbitMQ: Running"
else
    echo "❌ RabbitMQ: Failed"
fi

echo ""
echo "📊 Monitoring URLs:"
echo "Grafana: http://localhost:3000 (admin/admin)"
echo "Prometheus: http://localhost:9090"
echo "Flower: http://localhost:5555"
echo "RabbitMQ: http://localhost:15672 (guest/guest)"
echo ""
echo "🎯 API Endpoints:"
echo "Tax God: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
echo "Advanced Tax: http://localhost:8000/api/v1/advanced/query"
```

---

## 🎉 Success Checklist

- [ ] `docker-compose up -d --build` completes without errors
- [ ] `http://localhost:8000/health` returns healthy status
- [ ] `http://localhost:8000/api/docs` shows interactive API documentation
- [ ] Database connections work (check logs)
- [ ] Celery workers are processing tasks
- [ ] Grafana dashboards load properly
- [ ] Advanced tax queries return intelligent responses

**Local Docker deployment complete!** 🎉

**Ready to scale to cloud or deploy anywhere Docker runs.**