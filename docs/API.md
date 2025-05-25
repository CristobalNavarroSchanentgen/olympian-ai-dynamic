# Olympian AI API Documentation

## 🏛️ API Overview

The Olympian AI API provides comprehensive endpoints for service discovery, configuration management, chat operations, and system monitoring.

**Base URL**: `http://localhost:8000/api`

## 🔑 Authentication

Currently, the API uses optional JWT authentication. When enabled:

```bash
Authorization: Bearer <your-jwt-token>
```

## 📚 API Endpoints

### Service Discovery

#### Trigger Discovery Scan

```http
GET /api/discovery/scan
```

Triggers a comprehensive service discovery scan.

**Response**:
```json
{
  "status": "scanning",
  "message": "Service discovery scan initiated"
}
```

#### Get Discovery Status

```http
GET /api/discovery/status
```

Returns current discovery status and results.

**Response**:
```json
{
  "status": "active",
  "discovered_services": {
    "ollama": {
      "endpoints": ["http://localhost:11434"],
      "models": [{"name": "llama2:7b", "size": 3826793472}],
      "capabilities": {"version": "0.1.0", "gpu": true}
    },
    "mcp_servers": {
      "available": [{"id": "filesystem_3000", "type": "filesystem"}],
      "configured": []
    }
  },
  "service_health": {
    "ollama_http://localhost:11434": true,
    "system": {"cpu_ok": true, "memory_ok": true}
  }
}
```

### Ollama Integration

#### Discover Ollama Instances

```http
GET /api/ollama/discover
```

Discovers available Ollama instances on the network.

#### Get Available Models

```http
GET /api/ollama/models?endpoint=http://localhost:11434
```

**Query Parameters**:
- `endpoint` (optional): Specific Ollama endpoint

**Response**:
```json
{
  "endpoint": "http://localhost:11434",
  "models": [
    {
      "name": "llama2:7b",
      "modified_at": "2024-01-01T00:00:00Z",
      "size": 3826793472
    }
  ]
}
```

#### Chat with Model

```http
POST /api/ollama/chat
```

**Request Body**:
```json
{
  "model": "llama2:7b",
  "message": "Hello, Oracle!",
  "system_prompt": "You are a helpful assistant.",
  "temperature": 0.7,
  "context": [
    {"role": "user", "content": "Previous message"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

### MCP Management

#### List Available Tools

```http
GET /api/mcp/tools
```

**Response**:
```json
{
  "tools_by_server": {
    "filesystem_3000": ["read_file", "write_file", "list_directory"],
    "git_3001": ["clone", "commit", "push"]
  },
  "all_tools": [
    {"server_id": "filesystem_3000", "tool_name": "read_file"}
  ],
  "total_tools": 6
}
```

#### Execute Tool

```http
POST /api/mcp/tools/execute
```

**Request Body**:
```json
{
  "server_id": "filesystem_3000",
  "tool_name": "read_file",
  "parameters": {
    "path": "/path/to/file.txt"
  }
}
```

### Configuration Management

#### Get Dynamic Configuration

```http
GET /api/config/dynamic
```

Returns the current dynamic configuration including discovered services.

#### Update User Preferences

```http
PUT /api/config/preferences
```

**Request Body**:
```json
{
  "preferred_models": ["llama2:7b", "mistral:7b"],
  "custom_endpoints": ["http://remote-ollama:11434"],
  "disabled_services": ["webhook_discord"]
}
```

### Chat Operations

#### Send Chat Message

```http
POST /api/chat/message
```

**Request Body**:
```json
{
  "message": "Tell me about the stars",
  "model": "llama2:7b",
  "conversation_id": "uuid-here",
  "temperature": 0.7,
  "stream": true
}
```

#### List Conversations

```http
GET /api/chat/conversations?project_id=uuid&limit=20&offset=0
```

**Query Parameters**:
- `project_id` (optional): Filter by project
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset (default: 0)

### Project Management

#### Create Project

```http
POST /api/projects
```

**Request Body**:
```json
{
  "name": "Divine Creation",
  "description": "A sacred AI project",
  "model": "llama2:7b",
  "system_prompt": "You are a divine oracle.",
  "temperature": 0.7,
  "tools": ["read_file", "write_file"]
}
```

#### Update Project

```http
PUT /api/projects/{project_id}
```

**Request Body** (partial update):
```json
{
  "name": "Updated Project Name",
  "temperature": 0.8
}
```

### System Monitoring

#### Get System Resources

```http
GET /api/system/resources
```

**Response**:
```json
{
  "cpu": {
    "count": 8,
    "percent": 23.5,
    "frequency": {"current": 3600, "min": 800, "max": 4200}
  },
  "memory": {
    "total": 17179869184,
    "available": 8589934592,
    "percent": 50.0
  },
  "disk": {
    "total": 512110190592,
    "free": 256055095296,
    "percent": 50.0
  },
  "gpu": {
    "available": true,
    "type": "nvidia",
    "details": "NVIDIA GeForce RTX 3080, 10240MB"
  }
}
```

#### Optimize System

```http
POST /api/system/optimize
```

Triggers system optimization routines.

**Response**:
```json
{
  "status": "optimized",
  "optimizations": [
    "Garbage collection freed 1523 objects",
    "Cleared Ollama model cache",
    "Reduced connection pool sizes"
  ],
  "resource_usage_before": {"cpu": 75.2, "memory": 82.1},
  "resource_usage_after": {"cpu": 45.3, "memory": 65.4}
}
```

### Webhook Management

#### Generate Webhook

```http
POST /api/webhooks/generate
```

**Request Body**:
```json
{
  "name": "Supabase Events",
  "type": "supabase",
  "config": {
    "url": "https://project.supabase.co",
    "key": "your-anon-key",
    "table": "messages"
  },
  "events": ["INSERT", "UPDATE"],
  "active": true
}
```

#### Receive Webhook

```http
POST /api/webhooks/receive/{webhook_id}
```

Endpoint for receiving webhook events. Automatically generated for each webhook.

## 🌐 WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Types

#### Chat Message

```json
{
  "type": "chat",
  "content": "Hello, Oracle!",
  "model": "llama2:7b",
  "conversation_id": "uuid-here"
}
```

#### Configuration Update

```json
{
  "type": "config_update",
  "config_type": "model",
  "data": {
    "model": "llama2:7b"
  }
}
```

#### Service Discovery

```json
{
  "type": "service_discovery",
  "action": "scan"
}
```

### Server Events

#### Chat Response (Streaming)

```json
{
  "type": "chat_response",
  "content": "The stars are...",
  "model": "llama2:7b",
  "streaming": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Service Update

```json
{
  "type": "service_update",
  "service_type": "ollama",
  "status": "connected",
  "details": {
    "endpoints": ["http://localhost:11434"],
    "models": ["llama2:7b"]
  }
}
```

## 🚀 Rate Limiting

API endpoints are rate-limited based on system capacity:

- Default: 100 requests/minute
- Auto-adjusts based on CPU/memory usage
- WebSocket connections: 10 per IP

## 🔐 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here",
  "status_code": 400,
  "type": "validation_error"
}
```

**Common Status Codes**:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error

## 📝 Examples

### Complete Chat Flow

```python
import httpx
import asyncio
import websockets
import json

async def chat_example():
    # 1. Create conversation
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/chat/conversations",
            json={
                "title": "Test Conversation",
                "model": "llama2:7b"
            }
        )
        conversation = response.json()
    
    # 2. Connect WebSocket
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # 3. Send message
        await ws.send(json.dumps({
            "type": "chat",
            "content": "Tell me about Zeus",
            "model": "llama2:7b",
            "conversation_id": conversation["id"]
        }))
        
        # 4. Receive streaming response
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            if data["type"] == "chat_response":
                print(data["content"], end="", flush=True)
                
                if not data.get("streaming"):
                    break

asyncio.run(chat_example())
```

### Service Discovery Flow

```bash
# Trigger discovery
curl -X GET http://localhost:8000/api/discovery/scan

# Check status
curl -X GET http://localhost:8000/api/discovery/status

# Get discovered Ollama models
curl -X GET http://localhost:8000/api/ollama/models/all
```

---

For more examples and client libraries, visit our [GitHub repository](https://github.com/olympian-ai/olympian-ai-dynamic). ⚡