# Tax God Commands

## Local Development

```bash
cd /Users/enzogaroche/tax-god-copilot
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
cd /Users/enzogaroche/tax-god-copilot
pytest -q
```

## Compile Check

```bash
python3 -m compileall -q app
```

## Docker Stack

```bash
cd /Users/enzogaroche/tax-god-copilot
docker-compose up -d --build
docker-compose ps
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
```

## Celery Service Control

```bash
docker-compose restart celery-worker
docker-compose restart celery-beat
```

## Health / Metrics

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl -i http://localhost:8000/readiness
curl http://localhost:8000/metrics
```

## Integration Endpoints

```bash
curl "http://localhost:8000/api/v1/integrations/list?user_id=current_user"
curl -X POST http://localhost:8000/api/v1/integrations/connect \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","user_id":"current_user"}'
```

## ROI Endpoints

```bash
curl -X POST http://localhost:8000/api/v1/analytics/roi/calculate \
  -H "Content-Type: application/json" \
  -d '{"investment_cost":60000,"incremental_revenue":240000}'

curl -X POST http://localhost:8000/api/v1/analytics/roi/project \
  -H "Content-Type: application/json" \
  -d '{"monthly_traffic":10000,"current_conversion_rate":0.02,"target_conversion_rate":0.03,"average_deal_value":1000,"close_rate":0.25,"investment_cost":60000}'
```

