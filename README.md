# Olympian AI - Divine AI Interface with Dynamic Service Discovery

Welcome to Olympian AI, where divine aesthetics meet cutting-edge AI orchestration. This project features a Zeus-inspired interface with powerful backend capabilities, dynamic configuration management, and production-ready Docker containerization with MongoDB persistence and Redis caching.

## 🏛️ Features

### Sacred Infrastructure ⚡
- **Production-Ready Dockerization** - Complete Docker setup with multi-stage builds
- **MongoDB Persistence** - Divine data storage with automatic schema validation
- **Redis Caching** - Lightning-fast caching for optimal performance
- **Automated Backups** - Scheduled backups with configurable retention
- **Monitoring Stack** - Prometheus, Grafana, and Loki for divine oversight

### Sacred Ollama Endpoint Management
- **Divine Oracle Registration** - Add and manage custom Ollama endpoints
- **Real-time Connectivity Testing** - Test individual or all endpoints with divine precision
- **Primary Oracle Selection** - Choose your primary endpoint with sacred golden styling
- **Priority-based Ordering** - Set endpoint priorities for optimal divine routing
- **Advanced Configuration** - Timeouts, naming, enable/disable controls
- **Status Monitoring** - Real-time connection status and performance metrics

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
- **Sacred Configuration** page for advanced endpoint management

### Backend Capabilities
- FastAPI with async support
- Dynamic endpoint registration
- Automatic webhook generation
- MCP client implementation
- Ollama integration with model discovery
- **MongoDB Integration** with Beanie ODM
- **Redis Caching** for enhanced performance

## 🚀 Quick Start

### Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/CristobalNavarroSchanentgen/olympian-ai-dynamic.git
cd olympian-ai-dynamic

# Copy environment file
cp .env.example .env

# Start all services with Docker
make docker-up

# View logs
make docker-logs

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Setup

#### Backend Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend
cd backend

# Create virtual environment
uv venv

# Install dependencies (including MongoDB and Redis)
uv pip install -r requirements.txt

# Copy configuration files
cp .env.example .env
cp config.yaml.example config.yaml

# Run with auto-discovery
uvx --from uvicorn uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

## 🐳 Docker Commands

```bash
# Build images
make docker-build

# Start services
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Access MongoDB shell
make mongodb-shell

# Access Redis CLI
make redis-cli

# Backup MongoDB
make mongodb-backup

# Health check all services
make health-check

# Production deployment
make docker-prod
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          React Frontend                  │
│  - Divine Dialogue Interface             │
│  - Sacred Ollama Management UI          │
│  - Dynamic Configuration UI              │
│  - Real-time Updates via WebSocket      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│       Python Backend (FastAPI)           │
│  - Enhanced Ollama Configuration API     │
│  - Service Discovery Engine              │
│  - MongoDB Integration (Beanie ODM)      │
│  - Redis Caching Layer                   │
│  - WebSocket Handler                     │
│  - Auto-scaling Resources               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│         Infrastructure Services          │
│  - MongoDB (Data Persistence)            │
│  - Redis (Caching & Sessions)            │
│  - Multiple Ollama Instances             │
│  - MCP Servers                          │
│  - Nginx (Reverse Proxy)                │
│  - Monitoring Stack                      │
└─────────────────────────────────────────┘
```

## 🔧 Configuration

### Environment Variables

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=olympian_ai
MONGODB_USERNAME=olympian_app
MONGODB_PASSWORD=your-secure-password

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your-redis-password
REDIS_TTL=3600

# Security
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Service Discovery
DISCOVERY_ENABLED=true
DISCOVERY_SCAN_INTERVAL=30
```

### MongoDB Collections

- **conversations** - Chat history with validation
- **users** - User accounts and preferences
- **services** - Discovered services and health status
- **models** - Available AI models
- **api_keys** - API key management

### Redis Usage

- **Session Management** - User sessions and auth tokens
- **Cache Layer** - API responses and computed results
- **Rate Limiting** - Request throttling
- **Real-time Data** - WebSocket state management

## 📡 API Endpoints

### Discovery
- `GET /api/discovery/scan` - Trigger service scan
- `GET /api/discovery/status` - Get discovery status
- `GET /api/config/dynamic` - Get current configuration

### Sacred Ollama Management
- `GET /api/ollama/config/endpoints` - List all Ollama endpoints
- `POST /api/ollama/config/endpoints` - Add new endpoint
- `PUT /api/ollama/config/endpoints/{url}` - Update endpoint
- `DELETE /api/ollama/config/endpoints/{url}` - Remove endpoint
- `POST /api/ollama/config/endpoints/test` - Test single endpoint
- `POST /api/ollama/config/endpoints/test-all` - Test all endpoints
- `POST /api/ollama/config/endpoints/set-primary` - Set primary oracle

### Services
- `GET /api/ollama/discover` - Discover Ollama instances
- `GET /api/mcp/discover` - Discover MCP servers
- `GET /api/system/resources` - Get system resources
- `GET /api/health` - Health check endpoint

### Chat & Projects
- `POST /api/chat/message` - Send chat message
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project

## ⚡ Production Features

### High Availability
- **Load Balancing** - Nginx reverse proxy with upstream configuration
- **Health Checks** - Automatic container health monitoring
- **Auto-restart** - Failed services automatically recover
- **Resource Limits** - CPU and memory constraints for stability

### Security
- **Non-root Containers** - Enhanced security posture
- **Network Isolation** - Custom bridge network
- **Secret Management** - Environment-based configuration
- **CORS Protection** - Configurable origin restrictions

### Monitoring & Logging
- **Prometheus** - Metrics collection
- **Grafana** - Visual dashboards
- **Loki** - Log aggregation
- **Promtail** - Log shipping

### Backup & Recovery
- **Automated Backups** - Scheduled MongoDB dumps
- **Point-in-time Recovery** - Redis persistence
- **Configuration Backups** - Version-controlled configs

## 📚 Documentation

- [Sacred Ollama Endpoint Management Guide](docs/sacred-ollama-endpoints.md)
- [Docker Deployment Guide](docs/docker-deployment.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Overview](ARCHITECTURE.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🛡️ Security Considerations

- Always change default passwords in production
- Use SSL/TLS for external access
- Configure firewall rules appropriately
- Regularly update Docker images
- Monitor logs for suspicious activity

## 🌟 The Divine Experience

Olympian AI transforms AI interaction into a divine experience. With production-ready Docker containerization, MongoDB persistence, and Redis caching, the system provides enterprise-grade reliability while maintaining the elegant, mythology-inspired interface.

Like Zeus commanding from Mount Olympus, you control powerful AI capabilities through an interface worthy of the gods themselves, now with the stability and performance of modern cloud infrastructure.

## 📜 License

MIT License - May the gods smile upon your code! 🏛️⚡