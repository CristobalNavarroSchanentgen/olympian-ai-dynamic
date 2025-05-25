"""API Routes for Olympian AI"""

from .discovery import router as discovery_router
from .ollama import router as ollama_router
from .ollama_config import router as ollama_config_router  # Sacred Ollama endpoint management
from .mcp import router as mcp_router
from .webhooks import router as webhook_router
from .system import router as system_router
from .config import router as config_router
from .chat import router as chat_router
from .projects import router as project_router

__all__ = [
    "discovery_router",
    "ollama_router",
    "ollama_config_router",  # Sacred Ollama configuration
    "mcp_router",
    "webhook_router",
    "system_router",
    "config_router",
    "chat_router",
    "project_router"
]