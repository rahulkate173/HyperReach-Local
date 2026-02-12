#!/bin/bash
#
# Cold Outreach Engine - Setup Script for Linux/macOS
# Installs dependencies and sets up the project
#

set -e

echo "================================"
echo "🚀 Cold Outreach Engine Setup"
echo "================================"
echo ""

# Detect OS
OS_TYPE=$(uname -s)
echo "Detected OS: $OS_TYPE"
echo ""

# Check if Python is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Check if uv is installed
echo "Checking for uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ uv installed"
else
    UV_VERSION=$(uv --version)
    echo "✓ $UV_VERSION found"
fi
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📁 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "⚙️  Activating virtual environment..."
source .venv/bin/activate
echo ""

# Install dependencies using uv
echo "📦 Installing dependencies..."
uv pip install -e .
echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data models logs
chmod 755 data models logs
echo "✓ Directories created"
echo ""

# Download model cache
echo "🔄 Preparing model cache directory..."
mkdir -p models/.cache
chmod 755 models/.cache
echo "✓ Cache directory ready"
echo ""

echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "To start the server, run:"
echo ""
echo "  source .venv/bin/activate"
echo "  python3 -m backend.api"
echo ""
echo "Or for development with auto-reload:"
echo ""
echo "  uv run uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "Then open your browser to: http://127.0.0.1:8000"
echo ""
echo "For chat interface: http://127.0.0.1:8000/chat"
echo ""
