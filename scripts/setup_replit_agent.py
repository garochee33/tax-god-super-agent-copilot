#!/usr/bin/env python3
"""
Tax God - Replit Agent Setup Script
Sets up Tax God as Trinity Agent #56 in Replit environment
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def setup_replit_environment():
    """Set up the Replit environment for Tax God"""
    print("🚀 Setting up Tax God Replit Environment")
    print("=" * 50)

    # Check if we're in Replit
    if not os.environ.get('REPLIT_ENVIRONMENT'):
        print("⚠️  Warning: Not running in Replit environment")
        print("    Some features may not work correctly")
    else:
        print("✅ Running in Replit environment")

    # Create necessary directories
    dirs = [
        "logs",
        "data",
        "cache",
        "temp",
        "uploads",
        "exports"
    ]

    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"📁 Created directory: {dir_name}")

    # Set up Python virtual environment
    if not Path("venv").exists():
        print("📦 Creating Python virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    # Activate virtual environment and install dependencies
    pip_path = Path("venv/bin/pip")
    python_path = Path("venv/bin/python")

    if pip_path.exists():
        print("📦 Installing Python dependencies...")

        # Upgrade pip
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)

        # Install requirements
        if Path("requirements.txt").exists():
            subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        else:
            print("⚠️  requirements.txt not found, installing basic dependencies...")
            basic_deps = [
                "fastapi", "uvicorn", "pydantic", "sqlalchemy", "alembic",
                "redis", "python-multipart", "python-jose", "passlib",
                "aiofiles", "prometheus-client", "openai", "anthropic"
            ]
            subprocess.run([str(pip_path), "install"] + basic_deps, check=True)

    # Set up Node.js if package.json exists
    if Path("package.json").exists():
        print("📦 Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], check=True)

    # Set up environment variables
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env template...")
        env_template = """
# Tax God v3.0 Environment Configuration
# Set these values in Replit Secrets or .env file

# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-here
APP_VERSION=3.0.0

# Database (Replit provides these)
DATABASE_URL=${REPLIT_DB_URL}
REDIS_URL=${REPLIT_REDIS_URL}

# AI API Keys (Set in Replit Secrets)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Trinity Consortium
TRINITY_AGENT_ID=tax-god
TRINITY_AUTHORITY_LEVEL=4
TRINITY_ENVIRONMENT=replit

# Optional Integrations
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
QUICKBOOKS_CLIENT_ID=
QUICKBOOKS_CLIENT_SECRET=

# Cost Governance
COST_SOFT_LIMIT_PER_QUERY=0.50
COST_SOFT_LIMIT_PER_CLIENT_MONTH=100.00
COST_HARD_LIMIT_DAILY=200.00
"""
        env_file.write_text(env_template.strip())
        print("✅ Created .env template (set your API keys)")

    print("\n✅ Replit environment setup complete!")
    return True

def initialize_trinity_agent():
    """Initialize Tax God as a Trinity Consortium agent"""
    print("\n🤖 Initializing Trinity Agent #56 - Tax God")
    print("=" * 50)

    # Load agent configuration
    config_file = Path(".replit-agent.json")
    if not config_file.exists():
        print("❌ Agent configuration not found")
        return False

    try:
        with open(config_file) as f:
            config = json.load(f)

        print(f"✅ Agent: {config['name']}")
        print(f"✅ Agent ID: {config['agentId']}")
        print(f"✅ Trinity Role: {config['trinityRole']}")
        print(f"✅ Capabilities: {len(config['capabilities'])}")

        # Validate algorithms
        algorithms = config.get('algorithms', {})
        for algo_name, algo_config in algorithms.items():
            status = algo_config.get('status', 'unknown')
            print(f"✅ Algorithm {algo_name}: {status}")

        # Check API endpoints
        endpoints = config.get('apiEndpoints', {})
        print(f"✅ API Endpoints: {len(endpoints)} configured")

        print("\n✅ Trinity Agent initialization complete!")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize Trinity Agent: {e}")
        return False

def test_agent_system():
    """Test the agent system components"""
    print("\n🧪 Testing Agent System Components")
    print("=" * 50)

    # Test Python imports
    try:
        import sys
        sys.path.insert(0, '.')

        # Test core algorithms
        print("Testing DTDA...")
        from specs.algorithms.dtda import DynamicTaskDecompositionAlgorithm
        dtda = DynamicTaskDecompositionAlgorithm()
        dtda.decompose_task("Test tax query", {})
        print("✅ DTDA: Working")

        print("Testing IMRA...")
        from specs.algorithms.imra import IntelligentMemoryRetrievalAlgorithm, RetrievalContext
        imra = IntelligentMemoryRetrievalAlgorithm()
        context = RetrievalContext(query="test", client_id="test")
        imra.retrieve_context(context)
        print("✅ IMRA: Working")

        print("Testing SHVA...")
        from specs.algorithms.shva import SelfHealingValidationAlgorithm
        shva = SelfHealingValidationAlgorithm()
        test_data = {"content": "Test response", "task_type": "tax_analysis"}
        shva.validate_output(test_data, "tax_analysis")
        print("✅ SHVA: Working")

        # Test advanced orchestrator
        print("Testing Advanced Orchestrator...")
        from app.services.advanced_orchestrator import AdvancedTaxOrchestrator  # noqa: F401
        print("✅ Advanced Orchestrator: Import successful")

        print("\n✅ All agent system components working!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def create_startup_script():
    """Create a startup script for easy launching"""
    print("\n📜 Creating Startup Script")
    print("=" * 50)

    startup_script = """#!/bin/bash
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
"""

    script_path = Path("start_replit.sh")
    script_path.write_text(startup_script)
    script_path.chmod(0o755)

    print("✅ Created startup script: start_replit.sh")
    print("💡 Run with: ./start_replit.sh")

def main():
    """Main setup function"""
    print("🎭 Tax God v3.0 - Replit Agent Setup")
    print("Trinity Agent #56 - Tax, Financial & Legal Advisor")
    print("=" * 60)

    success = True

    # Setup environment
    if not setup_replit_environment():
        success = False

    # Initialize Trinity agent
    if not initialize_trinity_agent():
        success = False

    # Test system
    if not test_agent_system():
        success = False

    # Create startup script
    create_startup_script()

    if success:
        print("\n🎉 Tax God Replit Agent Setup Complete!")
        print("=" * 60)
        print("🤖 Trinity Agent #56 is ready for operation")
        print("🚀 Start with: ./start_replit.sh")
        print("📊 Monitor at: http://localhost:8000/health")
        print("📋 API docs at: http://localhost:8000/api/docs")
        print("")
        print("💡 Tax God can now:")
        print("   • Process complex tax queries with DTDA decomposition")
        print("   • Retrieve contextual information with IMRA memory")
        print("   • Validate responses with SHVA self-healing")
        print("   • Spawn specialized sub-agents for complex scenarios")
        print("   • Integrate with Trinity Consortium orchestration")
        print("=" * 60)
    else:
        print("\n❌ Setup completed with errors")
        print("Check the output above for specific issues")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
