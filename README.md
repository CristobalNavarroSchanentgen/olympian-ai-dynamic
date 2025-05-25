# Olympian AI - Divine AI Interface with Dynamic Service Discovery

Welcome to Olympian AI, where divine aesthetics meet cutting-edge AI orchestration. This project features a Zeus-inspired interface with powerful backend capabilities and fully dynamic configuration management.

## 🏛️ Features

### Dynamic Service Discovery
- **Auto-discovery** of Ollama, MCP servers, Redis, and webhook opportunities
- **Real-time configuration** updates as services come online/offline
- **Intelligent resource allocation** based on system capabilities
- **Service health monitoring** with auto-recovery

### Divine Interface
- Zeus/Olympian themed chat interface
- Multiple generation modes (image, video, audio, code, documents)
- Project mode with persistent configurations
- Real-time WebSocket communication
- TypeScript execution environment

### Backend Capabilities
- FastAPI with async support
- Dynamic endpoint registration
- Automatic webhook generation
- MCP client implementation
- Ollama integration with model discovery

## 🚀 Quick Start

### Backend Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend
cd backend

# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt

# Run with auto-discovery
uvx --from uvicorn uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          React Frontend                  │
│  - Divine Dialogue Interface             │
│  - Dynamic Configuration UI              │
│  - Real-time Updates via WebSocket      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│       Python Backend (FastAPI)           │
│  - Service Discovery Engine              │
│  - Dynamic Configuration Management      │
│  - WebSocket Handler                     │
│  - Auto-scaling Resources               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│         External Services                │
│  - Ollama (LLM)                         │
│  - MCP Servers                          │
│  - Redis                                │
│  - Webhooks                             │
└─────────────────────────────────────────┘
```

## 🔧 Configuration

The system automatically discovers and configures services. Manual configuration is minimal:

```yaml
# config.yaml - Most settings are auto-generated
server:
  host: "0.0.0.0"
  port: 8000
  discovery:
    enabled: true
    scan_interval: 30

# User preferences persist across discoveries
user_preferences:
  preferred_models: []
  disabled_services: []
```

## 📡 API Endpoints

### Discovery
- `GET /api/discovery/scan` - Trigger service scan
- `GET /api/discovery/status` - Get discovery status
- `GET /api/config/dynamic` - Get current configuration

### Services
- `GET /api/ollama/discover` - Discover Ollama instances
- `GET /api/mcp/discover` - Discover MCP servers
- `GET /api/system/resources` - Get system resources

### Chat & Projects
- `POST /api/chat/message` - Send chat message
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project

## 🌟 The Divine Experience

Olympian AI transforms AI interaction into a divine experience. The system automatically adapts to your environment, discovering and configuring services without manual intervention. Like Zeus commanding from Mount Olympus, you control powerful AI capabilities through an elegant, mythology-inspired interface.

## 📜 License

MIT License - May the gods smile upon your code!
