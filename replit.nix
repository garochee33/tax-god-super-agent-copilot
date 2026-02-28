# Replit Runtime Environment for Tax God v3.0
# Trinity Agent #56 - Tax, Financial & Legal Advisor

{ pkgs }: {
  deps = [
    # Python and core dependencies
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv

    # System dependencies
    pkgs.postgresql
    pkgs.redis
    pkgs.nodejs
    pkgs.yarn

    # Development tools
    pkgs.git
    pkgs.curl
    pkgs.wget
    pkgs.unzip

    # Build tools
    pkgs.gcc
    pkgs.gnumake
    pkgs.pkg-config

    # Libraries
    pkgs.libffi
    pkgs.openssl
    pkgs.zlib
    pkgs.bzip2
    pkgs.xz
    pkgs.sqlite

    # For PDF processing and other utilities
    pkgs.poppler_utils
    pkgs.imagemagick
    pkgs.ffmpeg

    # For vector databases and AI
    pkgs.pytorch
    pkgs.cudaPackages.cudatoolkit
  ];

  # Environment variables
  env = {
    PYTHONPATH = ".";
    PYTHONUNBUFFERED = "1";
    PYTHONDONTWRITEBYTECODE = "1";

    # Replit-specific settings
    REPLIT_ENVIRONMENT = "production";
    REPLIT_DB_URL = builtins.getEnv "REPLIT_DB_URL";
    REPLIT_REDIS_URL = builtins.getEnv "REPLIT_REDIS_URL";

    # Tax God settings
    TAX_GOD_VERSION = "3.0.0";
    TAX_GOD_AGENT_ID = "tax-god";
    TAX_GOD_ENVIRONMENT = "replit";

    # Trinity Consortium integration
    TRINITY_AGENT_ID = "tax-god";
    TRINITY_AUTHORITY_LEVEL = "4";
    TRINITY_SPECIALIZATION = "tax-finance-legal";
  };

  # Shell hooks
  shellHook = ''
    echo "🚀 Tax God v3.0 - Replit Environment Ready"
    echo "🤖 Trinity Agent #56 - Tax, Financial & Legal Advisor"
    echo ""

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      echo "📦 Creating Python virtual environment..."
      python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install/upgrade pip
    pip install --upgrade pip

    # Install dependencies if requirements.txt exists
    if [ -f "requirements.txt" ]; then
      echo "📦 Installing Python dependencies..."
      pip install -r requirements.txt
    fi

    # Install Node.js dependencies if package.json exists
    if [ -f "package.json" ]; then
      echo "📦 Installing Node.js dependencies..."
      npm install
    fi

    echo ""
    echo "✅ Environment setup complete!"
    echo "💡 Use 'python3 -m uvicorn app.main:app --reload' to start development server"
    echo "🌐 Production server will run on port 8000"
    echo ""
  '';
}