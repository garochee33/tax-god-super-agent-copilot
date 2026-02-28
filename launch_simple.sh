#!/bin/bash
# Tax God v3.0 - Simple Docker Launch Script
# For when docker-compose command detection fails

echo "🚀 Tax God v3.0 - Simple Docker Launch"
echo "🤖 Trinity Agent #56 - Tax, Financial & Legal Advisor"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys!"
    echo "   Add: OPENAI_API_KEY=sk-your-key"
    echo "   Add: ANTHROPIC_API_KEY=sk-ant-your-key"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

echo "🐳 Starting Docker containers..."
echo "   This will take 2-5 minutes on first run..."
echo ""

# Try the most common Docker Compose commands
if docker compose version 2>/dev/null; then
    echo "Using: docker compose (new version)"
    DOCKER_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    echo "Using: docker-compose (old version)"
    DOCKER_CMD="docker-compose"
else
    echo "❌ Docker Compose not found!"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Manual commands to run after installation:"
    echo "  docker compose up -d --build"
    echo "  # or"
    echo "  docker-compose up -d --build"
    exit 1
fi

# Launch services
$DOCKER_CMD up -d --build

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check if services are running
echo "🔍 Checking service status..."
$DOCKER_CMD ps

echo ""
echo "🎉 Tax God should be running!"
echo "=============================="
echo ""
echo "🌐 Access URLs:"
echo "   Tax God API:    http://localhost:8000"
echo "   API Docs:       http://localhost:8000/api/docs"
echo "   Health Check:   http://localhost:8000/health"
echo ""
echo "🧪 Test commands:"
echo "   curl http://localhost:8000/health"
echo "   docker compose logs -f api  # or docker-compose logs -f api"
echo ""
echo "📊 Monitoring:"
echo "   Grafana:        http://localhost:3000 (admin/admin)"
echo "   Prometheus:     http://localhost:9090"
echo ""
echo "🔧 Management:"
echo "   Stop:  docker compose down"
echo "   Logs:  docker compose logs -f"
echo ""
echo "🚀 Ready for tax AI processing!"