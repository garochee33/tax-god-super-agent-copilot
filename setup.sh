#!/bin/bash
# Tax God Super Agent Co-Pilot — One-Command Setup
# Run: ./setup.sh
set -e

echo "🏛️  Tax God Super Agent Co-Pilot — Setup"
echo "========================================="

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3.11+ required. Install: brew install python@3.11"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PY_VERSION"

# Check Postgres
if ! command -v psql &>/dev/null; then
    echo "❌ PostgreSQL required. Install: brew install postgresql@15 && brew services start postgresql@15"
    exit 1
fi
echo "✅ PostgreSQL found"

# Check Redis
if ! command -v redis-cli &>/dev/null; then
    echo "❌ Redis required. Install: brew install redis && brew services start redis"
    exit 1
fi
echo "✅ Redis found"

# Create venv
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install deps
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install stripe -q
echo "✅ Dependencies installed"

# Setup .env
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    # Set local dev DATABASE_URL
    DB_USER=$(whoami)
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://${DB_USER}@localhost:5432/taxgod|" .env 2>/dev/null || \
    sed -i "s|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://${DB_USER}@localhost:5432/taxgod|" .env
    sed -i '' "s|REDIS_URL=.*|REDIS_URL=redis://localhost:6379/0|" .env 2>/dev/null || \
    sed -i "s|REDIS_URL=.*|REDIS_URL=redis://localhost:6379/0|" .env
    echo "✅ .env created — edit to add your API keys"
else
    echo "✅ .env already exists"
fi

# Create database
echo "🗄️  Setting up database..."
createdb taxgod 2>/dev/null || echo "  (database already exists)"

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head
echo "✅ Database ready"

echo ""
echo "========================================="
echo "✅ Setup complete!"
echo ""
echo "To start the app:"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Then open: http://localhost:8000"
echo "Register a new account to get a 7-day free trial."
echo ""
echo "For Stripe payments, add your keys to .env:"
echo "  STRIPE_SECRET_KEY=sk_live_..."
echo "  STRIPE_PUBLISHABLE_KEY=pk_live_..."
echo "  STRIPE_PRICE_MONTHLY=price_..."
echo "========================================="
