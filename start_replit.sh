#!/bin/bash
# Tax God v3.0 - Replit Startup Script
# Trinity Agent #56 - Tax, Financial & Legal Advisor

echo "🚀 Starting Tax God v3.0"
echo "🤖 Trinity Agent #56 - Tax, Financial & Legal Advisor"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found"
fi

# Set environment variables
export PYTHONPATH="."
export TAX_GOD_VERSION="3.0.0"
export TRINITY_AGENT_ID="tax-god"

echo "🌐 Starting FastAPI server on port 8000..."
echo "📊 Health check: http://localhost:8000/health"
echo "📋 API docs: http://localhost:8000/api/docs"
echo ""

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
