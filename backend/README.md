# Olympian AI Backend

## 🏛️ Divine Backend Architecture

The Olympian AI backend is a sophisticated service orchestration system with dynamic discovery and configuration capabilities.

## 🚀 Quick Start

### Using UV (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Using Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

## 🔧 Configuration

1. Copy `.env.example` to `.env`
2. Copy `config.yaml.example` to `config.yaml`
3. The system will auto-discover services and update configuration

## 🏗️ Architecture

### Core Components

- **Service Discovery Engine**: Automatically finds and configures services
- **WebSocket Manager**: Real-time bidirectional communication
- **Dynamic Configuration**: Auto-generates optimal settings
- **Service Integration**: Ollama, MCP, webhooks, and more

### API Structure

```
/api/
├── discovery/     # Service discovery endpoints
├── ollama/        # LLM integration
├── mcp/           # Model Context Protocol
├── webhooks/      # Event management
├── system/        # Resource monitoring
├── config/        # Configuration management
├── chat/          # Chat operations
└── projects/      # Workspace management
```

## 🔌 Service Integration

### Ollama
- Auto-discovers instances on ports 11434, 8080
- Dynamically fetches available models
- Supports multiple concurrent instances

### MCP Servers
- Filesystem operations
- Git integration
- GitHub connectivity
- Custom tool execution

### Webhooks
- Supabase real-time events
- Mattermost integration
- Discord notifications
- Generic webhook support

## 📊 Monitoring

- Health check: `GET /health`
- System resources: `GET /api/system/resources`
- Service status: `GET /api/discovery/status`

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app
```

## 🔒 Security

- JWT authentication
- Dynamic CORS configuration
- Rate limiting with auto-adjustment
- Webhook signature verification

## 📝 Development

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy .
```

## 🌟 Features

- **Zero Configuration**: Services are discovered automatically
- **Hot Reload**: Configuration updates without restart
- **Scalable**: Resource allocation based on system capacity
- **Extensible**: Easy to add new service integrations
- **Observable**: Comprehensive logging and monitoring

## 🛠️ Troubleshooting

### Service Discovery Issues
1. Check network permissions
2. Verify service ports are open
3. Review discovery logs in `logs/`

### Performance Optimization
1. Run `POST /api/system/optimize`
2. Check resource limits: `GET /api/system/limits`
3. Monitor capacity: `GET /api/system/capacity`

## 📚 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit PR with clear description

---

May the gods of code smile upon your contributions! ⚡