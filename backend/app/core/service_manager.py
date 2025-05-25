"""Global Service Manager - Centralized service management for Olympian AI"""
from typing import Optional
from loguru import logger

# Global service instances
_ollama_service: Optional['OllamaService'] = None
_mcp_service: Optional['MCPService'] = None
_project_service: Optional['ProjectService'] = None


def set_ollama_service(service: 'OllamaService'):
    """Set the global Ollama service instance"""
    global _ollama_service
    _ollama_service = service
    logger.info("🎯 Global Ollama service registered")


def set_mcp_service(service: 'MCPService'):
    """Set the global MCP service instance"""
    global _mcp_service
    _mcp_service = service
    logger.info("🔌 Global MCP service registered")


def set_project_service(service: 'ProjectService'):
    """Set the global Project service instance"""
    global _project_service
    _project_service = service
    logger.info("📁 Global Project service registered")


def get_ollama_service() -> Optional['OllamaService']:
    """Get the global Ollama service instance"""
    return _ollama_service


def get_mcp_service() -> Optional['MCPService']:
    """Get the global MCP service instance"""
    return _mcp_service


def get_project_service() -> Optional['ProjectService']:
    """Get the global Project service instance"""
    return _project_service


def are_services_ready() -> bool:
    """Check if all core services are initialized"""
    return _ollama_service is not None and _mcp_service is not None
