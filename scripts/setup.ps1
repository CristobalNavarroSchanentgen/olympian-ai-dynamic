# Olympian AI Setup Script for Windows
# Divine installation automation

Write-Host "`n🏛️  Welcome to Olympian AI Setup  🏛️" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Function to print colored output
function Write-Status {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning {
    param($Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Check for required tools
Write-Host "Checking prerequisites..."

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Status "Python found: $pythonVersion"
} catch {
    Write-Error "Python 3 is required but not installed"
    Write-Host "Please install Python from https://www.python.org/downloads/"
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Status "Node.js found: $nodeVersion"
} catch {
    Write-Error "Node.js is required but not installed"
    Write-Host "Please install Node.js from https://nodejs.org/"
    exit 1
}

# Check if uv is installed
try {
    uv --version | Out-Null
    Write-Status "uv is already installed"
} catch {
    Write-Warning "uv not found. Installing..."
    irm https://astral.sh/uv/install.ps1 | iex
    Write-Status "uv installed"
}

# Setup Backend
Write-Host "`nSetting up Backend..." -ForegroundColor Cyan
Set-Location backend

# Create virtual environment
if (-not (Test-Path ".venv")) {
    uv venv
    Write-Status "Virtual environment created"
}

# Activate virtual environment
& .venv\Scripts\Activate.ps1

# Install dependencies
Write-Status "Installing Python dependencies..."
uv pip install -r requirements.txt

# Copy example files
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Status "Created .env file"
}

if (-not (Test-Path "config.yaml")) {
    Copy-Item config.yaml.example config.yaml
    Write-Status "Created config.yaml file"
}

# Create necessary directories
New-Item -ItemType Directory -Force -Path data | Out-Null
New-Item -ItemType Directory -Force -Path logs | Out-Null
Write-Status "Created data and log directories"

Set-Location ..

# Setup Frontend
Write-Host "`nSetting up Frontend..." -ForegroundColor Cyan
Set-Location frontend

# Install dependencies
Write-Status "Installing Node.js dependencies..."
npm install

# Copy example files
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Status "Created .env file"
}

Set-Location ..

# Docker setup (optional)
try {
    docker --version | Out-Null
    docker-compose --version | Out-Null
    
    Write-Host "`nDocker detected. Setting up Docker configuration..." -ForegroundColor Cyan
    
    if (-not (Test-Path "docker-compose.override.yml")) {
        Copy-Item docker-compose.override.yml.example docker-compose.override.yml
        Write-Status "Created docker-compose.override.yml"
    }
    
    Write-Status "Docker setup complete"
} catch {
    Write-Warning "Docker not found. Skipping Docker setup."
}

# Final instructions
Write-Host "`n======================================" -ForegroundColor Green
Write-Host "🎆 Olympian AI Setup Complete! 🎆" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:"
Write-Host ""
Write-Host "1. Start the backend:" -ForegroundColor Yellow
Write-Host "   cd backend"
Write-Host "   .venv\Scripts\Activate.ps1"
Write-Host "   uvicorn main:app --reload"
Write-Host ""
Write-Host "2. Start the frontend (in a new terminal):" -ForegroundColor Yellow
Write-Host "   cd frontend"
Write-Host "   npm run dev"
Write-Host ""
Write-Host "3. Open http://localhost:5173 in your browser" -ForegroundColor Yellow
Write-Host ""
Write-Host "For Docker users:" -ForegroundColor Cyan
Write-Host "   docker-compose up"
Write-Host ""
Write-Host "May the gods smile upon your code! ⚡" -ForegroundColor Magenta
Write-Host ""