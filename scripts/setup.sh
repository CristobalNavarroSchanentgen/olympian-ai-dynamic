#!/bin/bash

# Olympian AI Setup Script
# Divine installation automation

set -e

echo ""
echo "🏛️  Welcome to Olympian AI Setup  🏛️"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check for required tools
echo "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION found"
else
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_status "Node.js $NODE_VERSION found"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_warning "uv not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    print_status "uv installed"
else
    print_status "uv is already installed"
fi

# Setup Backend
echo ""
echo "Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    uv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
source .venv/bin/activate || source .venv/Scripts/activate

# Install dependencies
print_status "Installing Python dependencies..."
uv pip install -r requirements.txt

# Copy example files
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Created .env file"
fi

if [ ! -f "config.yaml" ]; then
    cp config.yaml.example config.yaml
    print_status "Created config.yaml file"
fi

# Create necessary directories
mkdir -p data logs
print_status "Created data and log directories"

cd ..

# Setup Frontend
echo ""
echo "Setting up Frontend..."
cd frontend

# Install dependencies
print_status "Installing Node.js dependencies..."
npm install

# Copy example files
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Created .env file"
fi

cd ..

# Docker setup (optional)
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo ""
    echo "Docker detected. Setting up Docker configuration..."
    
    if [ ! -f "docker-compose.override.yml" ]; then
        cp docker-compose.override.yml.example docker-compose.override.yml
        print_status "Created docker-compose.override.yml"
    fi
    
    print_status "Docker setup complete"
else
    print_warning "Docker not found. Skipping Docker setup."
fi

# Final instructions
echo ""
echo "======================================"
echo "🎆 Olympian AI Setup Complete! 🎆"
echo "======================================"
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source .venv/bin/activate"
echo "   uvicorn main:app --reload"
echo ""
echo "2. Start the frontend (in a new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Open http://localhost:5173 in your browser"
echo ""
echo "For Docker users:"
echo "   docker-compose up"
echo ""
echo "May the gods smile upon your code! ⚡"
echo ""