# 🎭 Tax God v3.0 - Replit Agent Setup

**Trinity Agent #56 - Chief Tax, Financial & Legal Advisor**

This guide shows you how to deploy and run Tax God as a fully integrated Replit Agent within the Trinity Consortium's 55-agent orchestration system.

---

## 🚀 Quick Start

### 1. Fork & Setup
```bash
# Fork this Replit
# Or clone to your Replit workspace

# Run the setup script
python3 scripts/setup_replit_agent.py
```

### 2. Configure Secrets
In your Replit **Secrets** tab, set:
```
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
SECRET_KEY=generate-random-32-char-string
```

### 3. Start Tax God
```bash
# Use the startup script
./start_replit.sh

# Or manually
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access Tax God
- **Health Check**: `https://your-replit.replit.dev/health`
- **API Docs**: `https://your-replit.replit.dev/api/docs`
- **Advanced Tax API**: `https://your-replit.replit.dev/api/v1/advanced/query`

---

## 🤖 Trinity Agent Architecture

### Agent Profile
```
Agent ID: tax-god
Trinity Role: Chief Tax, Financial & Legal Advisor
Authority Level: 4 (High - Financial Decisions)
Cost/Task: $0.15
Capabilities: tax_analysis, financial_advice, legal_counsel, agent_spawning
```

### Core Algorithms
- **DTDA**: Dynamic Task Decomposition Algorithm
- **IMRA**: Intelligent Memory Retrieval Algorithm (5-tier)
- **SHVA**: Self-Healing Validation Algorithm

### Integration Points
- **Receives delegations** from: oracle, prophet, chancellor, warden, liaison
- **Delegates to**: oracle, researcher, auditor, engineer
- **Override authority**: Can only be overridden by warden
- **Communication**: RESTful APIs, WebSocket support

---

## 🛠️ Replit Configuration

### Files Created
- **`.replit`** - Replit environment configuration
- **`replit.nix`** - Nix runtime environment
- **`.replit-agent.json`** - Agent capabilities and Trinity integration
- **`scripts/setup_replit_agent.py`** - Automated setup script

### Environment Variables
```bash
# Replit Auto-Provides
REPLIT_DB_URL=postgresql://...
REPLIT_REDIS_URL=redis://...

# Tax God Specific
TAX_GOD_VERSION=3.0.0
TRINITY_AGENT_ID=tax-god
TRINITY_AUTHORITY_LEVEL=4

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Runtime Stack
- **Python 3.11** with FastAPI
- **PostgreSQL** (Replit managed)
- **Redis** (Replit managed)
- **Node.js** for frontend tooling
- **Nix** environment management

---

## 🔧 Advanced Setup

### Manual Environment Setup
```bash
# If auto-setup fails
cd /home/runner/tax-god-copilot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export SECRET_KEY="random-32-char-string"
```

### Database Setup
```bash
# Initialize database (if not auto-created)
source venv/bin/activate
alembic upgrade head

# Seed initial data (optional)
python3 scripts/seed_data.py
```

### Agent Registration
```bash
# Register with Trinity Consortium
curl -X POST https://your-trinity-coordinator/agent/register \
  -H "Content-Type: application/json" \
  -d @.replit-agent.json
```

---

## 🎯 Using Tax God Agent

### Basic Tax Query
```bash
curl -X POST https://your-replit.replit.dev/api/v1/advanced/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How can I optimize my S-Corp taxes?",
    "clientId": "client_123",
    "requireCitations": true
  }'
```

### Trinity Consortium Message
```bash
# Send Trinity-formatted message
curl -X POST https://your-replit.replit.dev/api/v1/trinity/message \
  -H "Content-Type: application/json" \
  -d '{
    "from": "oracle",
    "to": "tax-god",
    "type": "request",
    "payload": {
      "query": "Analyze tax implications of merger",
      "clientId": "enterprise_client"
    }
  }'
```

### Agent Spawning
```bash
# Request agent spawning for complex scenario
curl -X POST https://your-replit.replit.dev/api/v1/advanced/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Handle multi-state tax filing for CA, NY, TX",
    "allowSpawning": true,
    "context": {"multi_state": true}
  }'
```

---

## 📊 Monitoring & Health

### Health Endpoints
- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /health/detailed`
- **Advanced Health**: `GET /api/v1/advanced/health`
- **Metrics**: `GET /metrics`

### Trinity Agent Status
```bash
curl https://your-replit.replit.dev/api/v1/trinity/agent/tax-god/status
```

### Performance Metrics
- Query processing time
- Confidence scores
- Agent spawning statistics
- Cost tracking per task
- Error rates and recovery

---

## 🔄 Trinity Consortium Integration

### Message Flow
```
User → Trinity Coordinator → Tax God Agent → Processing Pipeline → Response
                           ↓
                    DTDA Decomposition → IMRA Memory → SHVA Validation
                           ↓
                    Sub-agent Spawning (if needed)
```

### Authority Hierarchy
```
Warden (Supreme) ← Tax God (Level 4) ← Oracle/Prophet (Level 3)
                                       ← Chancellor/Liaison (Level 2)
```

### Cost Management
- **Base Cost**: $0.15 per task
- **Algorithm Costs**: DTDA ($0.02), IMRA ($0.01), SHVA ($0.02)
- **Sub-agent Costs**: Additional $0.08-0.15 per spawned agent
- **Budget Limits**: Configurable per client/session

---

## 🧪 Testing the Agent

### Run Algorithm Tests
```bash
python3 test_algorithms.py
```

### Run Trinity Integration Tests
```bash
python3 test_trinity_integration.py
```

### Manual Testing
```bash
# Test basic functionality
curl https://your-replit.replit.dev/health

# Test advanced pipeline
curl -X POST https://your-replit.replit.dev/api/v1/advanced/decompose \
  -H "Content-Type: application/json" \
  -d '{"query": "Complex tax scenario"}'
```

---

## 🚀 Production Deployment

### Replit Deployment
1. **Push to main branch** - Auto-deploys
2. **Monitor logs** - Check Replit logs tab
3. **Scale resources** - Adjust Replit plan as needed
4. **Set up monitoring** - Configure uptime checks

### Performance Tuning
```bash
# Enable caching
export CACHE_ENABLED=true

# Set concurrency limits
export MAX_CONCURRENT_QUERIES=10

# Configure monitoring
export MONITORING_ENABLED=true
```

### Backup & Recovery
- **Database**: Replit-managed PostgreSQL with automatic backups
- **Redis**: Replit-managed with persistence
- **Code**: Git-based version control
- **Logs**: Replit log retention

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

**Database connection issues:**
```bash
# Check Replit database URL
echo $REPLIT_DB_URL

# Reset database
alembic downgrade base
alembic upgrade head
```

**AI API rate limits:**
```bash
# Check usage
curl https://your-replit.replit.dev/api/v1/advanced/health

# Reduce concurrency
export MAX_CONCURRENT_QUERIES=5
```

**Agent spawning failures:**
```bash
# Check agent status
curl https://your-replit.replit.dev/api/v1/trinity/agent/tax-god/status

# Review logs
tail logs/agent_spawn.log
```

---

## 📈 Scaling & Optimization

### Performance Optimization
- **Caching**: Enable Redis caching for repeated queries
- **Async Processing**: Use background tasks for complex operations
- **Model Selection**: Auto-select optimal model based on complexity
- **Batch Processing**: Group similar queries for efficiency

### Enterprise Features
- **Multi-tenancy**: Support multiple client organizations
- **Audit Trails**: Complete compliance logging
- **Load Balancing**: Distribute across multiple Replit instances
- **API Rate Limiting**: Prevent abuse and manage costs

### Cost Management
- **Budget Controls**: Per-client and system-wide limits
- **Model Optimization**: Use cheaper models for simple queries
- **Caching**: Reduce API calls through intelligent caching
- **Monitoring**: Track costs in real-time

---

## 🎯 Advanced Usage

### Custom Agent Behaviors
```typescript
// Extend agent capabilities
const customTaxGod = {
  ...taxGodAgent,
  customCapabilities: {
    industrySpecific: ["tech_startup", "real_estate", "healthcare"],
    regionalExpertise: ["california", "new_york", "texas"]
  }
};
```

### Integration with External Systems
```python
# Connect to accounting software
@app.post("/api/v1/integrations/quickbooks/sync")
async def sync_quickbooks_tax_data():
    # Sync tax data from QuickBooks
    # Process with Tax God algorithms
    # Return optimized recommendations
```

### Custom Workflows
```python
# Create tax filing workflow
@app.post("/api/v1/workflows/tax-filing")
async def create_tax_filing_workflow(tax_year: int, entity_type: str):
    # DTDA decomposition
    # IMRA context gathering
    # SHVA validation steps
    # Agent spawning for complexity
    # Timeline and deadline management
```

---

## 🤝 Contributing & Development

### Development Workflow
1. **Fork** the Replit
2. **Create feature branch** from main
3. **Test locally** with `python3 test_algorithms.py`
4. **Commit changes** with clear messages
5. **Test Trinity integration** with `python3 test_trinity_integration.py`
6. **Merge** via pull request

### Code Quality
- **TypeScript**: Strict typing for agent interfaces
- **Python**: Black formatting, mypy type checking
- **Testing**: 85%+ test coverage required
- **Documentation**: Auto-generated API docs

### Security
- **API Key Management**: Replit Secrets for all credentials
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: Built-in request throttling
- **Audit Logging**: Complete action tracking

---

## 📞 Support & Resources

### Documentation
- **API Docs**: Auto-generated at `/api/docs`
- **Health Checks**: `/health` and `/health/detailed`
- **Metrics**: `/metrics` (Prometheus format)

### Trinity Consortium
- **Agent Registry**: Connect to Trinity coordinator
- **Message Protocol**: RESTful + WebSocket support
- **Coordination**: Authority-based delegation system

### Community
- **Issues**: Report bugs and request features
- **Discussions**: Share integration patterns
- **Wiki**: Comprehensive setup guides

---

**Tax God v3.0 is now fully deployed as Trinity Agent #56! 🎉**

**Ready to handle enterprise tax scenarios with AI-powered intelligence, multi-agent coordination, and self-healing validation.**

**🌐 Access at: `https://your-replit.replit.dev`**