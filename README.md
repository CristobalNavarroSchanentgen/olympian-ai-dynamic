# Olympian AI - Divine AI Interface with Dynamic Service Discovery

Welcome to Olympian AI, where divine aesthetics meet cutting-edge AI orchestration. This project features a Zeus-inspired interface with powerful backend capabilities and fully dynamic configuration management.

## 🏛️ Features

### Sacred Ollama Endpoint Management ⚡
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
- **Enhanced Ollama configuration API** with testing and validation

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

## 🔥 Sacred Ollama Management

Access the **Sacred Configuration** → **Sacred Ollama** tab for advanced endpoint management:

### Adding Divine Oracles
1. Click **"Add Oracle"** 
2. Enter endpoint details:
   - URL: `http://your-ollama:11434`
   - Name: Custom display name
   - Priority: 0-100 (higher = more divine)
   - Timeout: Connection timeout seconds
3. Click **"Register Oracle"**

### Testing Divine Connectivity
- **Individual Test**: Click 🧪 next to any endpoint
- **Bulk Test**: Click **"Test All"** for comprehensive validation
- **Real-time Metrics**: View response times, model counts, versions

### Primary Oracle Management
- Click ⭐ next to any enabled endpoint to make it primary
- Primary oracle gets divine golden styling and priority routing

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
│  - Dynamic Configuration Management      │
│  - WebSocket Handler                     │
│  - Auto-scaling Resources               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│         External Services                │
│  - Multiple Ollama Instances (Custom)    │
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
  custom_endpoints: []  # Sacred Ollama endpoints
  manual_overrides:
    ollama_endpoints:   # Advanced endpoint configs
      "http://localhost:11434":
        name: "Local Divine Oracle"
        priority: 10
        timeout: 30
```

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

### Chat & Projects
- `POST /api/chat/message` - Send chat message
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project

## ⚡ Sacred Features Highlights

### User-Editable Endpoints
Users can now easily manage Ollama endpoints through the divine interface:
- Add custom endpoints beyond auto-discovery
- Test connectivity with real-time feedback
- Set priorities and configure timeouts
- Enable/disable endpoints as needed
- Designate primary oracles for optimal routing

### Real-time Testing
- Comprehensive connectivity validation
- Performance metrics (response time, model count)
- Error reporting with detailed messages
- Bulk testing for efficiency

### Divine UX Design
- Olympus gold and Zeus blue theming
- Animated interactions and status updates
- Responsive design for all devices
- Intuitive controls with sacred iconography

## 📚 Documentation

- [Sacred Ollama Endpoint Management Guide](docs/sacred-ollama-endpoints.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Architecture Overview](ARCHITECTURE.md)

## 🌟 The Divine Experience

Olympian AI transforms AI interaction into a divine experience. The system automatically adapts to your environment, discovering and configuring services without manual intervention. The new Sacred Ollama Endpoint Management elevates this experience, giving users divine control over their AI oracles while maintaining the elegant, mythology-inspired interface.

Like Zeus commanding from Mount Olympus, you control powerful AI capabilities through an interface worthy of the gods themselves.

## 📜 License

MIT License - May the gods smile upon your code! 🏛️⚡
