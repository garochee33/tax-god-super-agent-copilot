#!/bin/bash
# Tax God Super Agent Co-Pilot — Local Setup (fully automated)
# Run: ./setup.sh
set -e

echo ""
echo "🏛️  Tax God Super Agent Co-Pilot"
echo "   Local Sovereign Setup"
echo "════════════════════════════════════════"
echo ""

# ─── Prerequisites ───────────────────────────────────────────────────────────

check() { command -v "$1" &>/dev/null; }

if ! check python3; then
    echo "❌ Python 3.11+ required → brew install python@3.11"; exit 1
fi
echo "✅ Python $(python3 --version | cut -d' ' -f2)"

if ! check psql; then
    echo "📦 Installing PostgreSQL..."
    brew install postgresql@15 && brew services start postgresql@15
fi
echo "✅ PostgreSQL"

if ! check redis-cli; then
    echo "📦 Installing Redis..."
    brew install redis && brew services start redis
fi
echo "✅ Redis"

# Ensure services are running
brew services start postgresql@15 2>/dev/null || brew services start postgresql@18 2>/dev/null || true
brew services start redis 2>/dev/null || true

# ─── Virtual Environment ─────────────────────────────────────────────────────

if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install stripe -q 2>/dev/null || true
echo "✅ Dependencies installed"

# ─── Auto-Generate .env ──────────────────────────────────────────────────────

if [ ! -f ".env" ]; then
    echo ""
    echo "🔑 Generating secrets and .env..."

    SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    DB_USER=$(whoami)

    cat > .env << EOF
# Tax God — Local Configuration (auto-generated)
ENVIRONMENT=development
DEBUG=true
APP_VERSION=3.1.0
LOG_LEVEL=INFO

# Security (auto-generated — rotate in Settings)
SECRET_KEY=${SECRET_KEY}
INTEGRATION_ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Database (local)
DATABASE_URL=postgresql+asyncpg://${DB_USER}@localhost:5432/taxgod
REDIS_URL=redis://localhost:6379/0

# AI Keys (add yours in Settings page after launch)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Stripe (optional — for subscription billing)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_MONTHLY=

# OAuth Integrations (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/callback
QUICKBOOKS_CLIENT_ID=
QUICKBOOKS_CLIENT_SECRET=
QUICKBOOKS_REDIRECT_URI=http://localhost:8000/api/v1/integrations/callback

# Outreach (optional)
SENDGRID_API_KEY=
APOLLO_API_KEY=
EOF
    echo "✅ .env created with auto-generated secrets"
else
    echo "✅ .env exists"
fi

# ─── Database ────────────────────────────────────────────────────────────────

echo ""
createdb taxgod 2>/dev/null && echo "✅ Database 'taxgod' created" || echo "✅ Database 'taxgod' exists"

echo "🔄 Running migrations..."
alembic upgrade head 2>&1 | grep -E "Running|already"
echo "✅ Database ready"

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo "════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "  Start:  source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "  Open:   http://localhost:8000"
echo ""
echo "  Register an account → 7-day free trial starts."
echo "  Add your AI keys in ⚙️ Settings after login."
echo "════════════════════════════════════════"
echo ""
