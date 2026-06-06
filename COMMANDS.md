# Tax God Commands

## Local Development

```bash
# Activate venv + run
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Tests

```bash
# Full suite (46 tests)
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Individual modules
pytest tests/test_auth.py -v          # Auth (14 tests)
pytest tests/test_chat.py -v          # Chat/AI (6 tests)
pytest tests/test_documents.py -v     # Documents (7 tests)
pytest tests/test_analytics.py -v     # Analytics (8 tests)
pytest tests/test_e2e_pipeline.py -v  # E2E pipeline (1 test)

# Legacy tests
python3 test_algorithms.py
python3 test_trinity_integration.py
```

## Compile Check

```bash
python3 -m compileall -q app
```

## Lint

```bash
ruff check app/
ruff check app/ --fix   # auto-fix
```

## Docker Stack

```bash
docker-compose up -d --build
docker-compose ps
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
docker-compose down
```

## Celery Service Control

```bash
docker-compose restart celery-worker
docker-compose restart celery-beat
```

## Database

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## Health / Metrics

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl -i http://localhost:8000/readiness
curl http://localhost:8000/metrics
```

## Auth Endpoints

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecureP@ss1","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecureP@ss1"}'

# Dev token (development only)
curl -X POST http://localhost:8000/api/v1/auth/dev-token
```

## Clients (Agora) Endpoints

```bash
TOKEN="Bearer <access_token>"

# List clients
curl http://localhost:8000/api/v1/clients -H "Authorization: $TOKEN"

# Create client
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","email":"cfo@acme.com","filing_type":"business","status":"active"}'

# Update client
curl -X PATCH http://localhost:8000/api/v1/clients/<id> \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"notes":"Annual filing due March 15"}'

# Delete client
curl -X DELETE http://localhost:8000/api/v1/clients/<id> -H "Authorization: $TOKEN"
```

## Chat / AI Endpoints

```bash
TOKEN="Bearer <access_token>"

# Standard query
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"What is the standard deduction for 2024?","require_citations":true}'

# God Mode v3.0 (DTDA→IMRA→SHVA pipeline)
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"Multi-state tax analysis for S-Corp","use_god_mode":true}'

# Citation search
curl -X POST http://localhost:8000/api/v1/chat/citations/search \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"query":"IRC 199A","max_results":5}'
```

## Integration Endpoints

```bash
curl "http://localhost:8000/api/v1/integrations/list" -H "Authorization: $TOKEN"
curl -X POST http://localhost:8000/api/v1/integrations/connect \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"provider":"google"}'
```

## Analytics / ROI Endpoints

```bash
# ROI calculate
curl -X POST http://localhost:8000/api/v1/analytics/roi/calculate \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"investment_cost":60000,"incremental_revenue":240000}'

# ROI project
curl -X POST http://localhost:8000/api/v1/analytics/roi/project \
  -H "Authorization: $TOKEN" -H "Content-Type: application/json" \
  -d '{"monthly_traffic":10000,"current_conversion_rate":0.02,"target_conversion_rate":0.03,"average_deal_value":1000,"close_rate":0.25,"investment_cost":60000}'

# Usage analytics
curl http://localhost:8000/api/v1/analytics/usage -H "Authorization: $TOKEN"

# Circuit breaker status (admin only)
curl http://localhost:8000/api/v1/analytics/governance/circuit-breaker -H "Authorization: $TOKEN"
```
