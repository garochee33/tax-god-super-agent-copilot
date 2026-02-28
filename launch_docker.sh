#!/bin/bash
# Tax God v3.0 - Local Docker Launch Script
# Trinity Agent #56 - Tax, Financial & Legal Advisor

set -e

echo "🚀 Tax God v3.0 - Local Docker Launch"
echo "🤖 Trinity Agent #56 - Tax, Financial & Legal Advisor"
echo "🐳 Starting complete local development environment..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys before continuing!"
    echo "   Required: OPENAI_API_KEY and ANTHROPIC_API_KEY"
    echo ""
    echo "   Edit with: nano .env"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

# Check for required API keys
if ! grep -q "sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: No API keys found in .env file"
    echo "   Make sure OPENAI_API_KEY and ANTHROPIC_API_KEY are set"
    echo ""
    read -p "Press Enter to continue anyway..."
fi

echo "🏗️  Building and starting Docker containers..."
echo "   This may take a few minutes on first run..."
echo ""

# Function to get the correct Docker Compose command
get_docker_compose_cmd() {
    if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

# Get the correct command
DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
if [ -z "$DOCKER_COMPOSE_CMD" ]; then
    echo "❌ Error: Docker Compose not found!"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "Using: $DOCKER_COMPOSE_CMD"

# Build and start services
$DOCKER_COMPOSE_CMD up -d --build

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Function to check service
check_service() {
    local service=$1
    local url=$2
    local name=$3

    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name: Running at $url"
    else
        echo "❌ $name: Not responding at $url"
    fi
}

# Check core services
check_service "api" "http://localhost:8000/health" "Tax God API"
check_service "grafana" "http://localhost:3000" "Grafana"
check_service "prometheus" "http://localhost:9090" "Prometheus"
check_service "flower" "http://localhost:5555" "Flower"

# Check database connectivity
if $DOCKER_COMPOSE_CMD exec -T postgres pg_isready -U taxgod -d taxgod > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Connected"
else
    echo "❌ PostgreSQL: Connection failed"
fi

if $DOCKER_COMPOSE_CMD exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis: Connected"
else
    echo "❌ Redis: Connection failed"
fi

echo ""
echo "🎉 Tax God Local Docker Environment Ready!"
echo "==============================================="
echo ""
echo "🌐 Access Points:"
echo "   Tax God API:     http://localhost:8000"
echo "   API Docs:        http://localhost:8000/api/docs"
echo "   Health Check:    http://localhost:8000/health"
echo "   Advanced Tax:    http://localhost:8000/api/v1/advanced/query"
echo ""
echo "📊 Monitoring:"
echo "   Grafana:         http://localhost:3000 (admin/admin)"
echo "   Prometheus:      http://localhost:9090"
echo "   Flower:          http://localhost:5555"
echo "   RabbitMQ Admin:  http://localhost:15672 (guest/guest)"
echo ""
echo "🗄️  Database:"
echo "   PostgreSQL:      localhost:5432 (taxgod/taxgod123)"
echo "   Redis:           localhost:6379"
echo ""
echo "🧪 Quick Tests:"
echo "   curl http://localhost:8000/health"
echo "   curl -X POST http://localhost:8000/api/v1/advanced/decompose \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"query\": \"How do I file my taxes?\"}'"
echo ""
echo "🔧 Management Commands:"
echo "   View logs:       docker-compose logs -f"
echo "   Stop services:   docker-compose down"
echo "   Restart API:     docker-compose restart api"
echo ""
echo "📚 Documentation:"
echo "   Local Setup:     cat LOCAL_DOCKER_SETUP.md"
echo "   API Reference:   Visit http://localhost:8000/api/docs"
echo ""
echo "💡 Tax God is now running with:"
echo "   • DTDA, IMRA, SHVA core algorithms"
echo "   • Trinity Consortium agent integration"
echo "   • Enterprise-grade monitoring and logging"
echo "   • Complete tax processing pipeline"
echo ""
echo "🎯 Ready to process tax queries intelligently! 🚀"