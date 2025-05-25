"""Ollama Service - Communication with the Oracle"""
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx
from loguru import logger
import json

from ..core.config import settings


class OllamaService:
    """Service for interacting with Ollama instances"""
    
    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._model_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._default_endpoint: Optional[str] = None
    
    async def initialize(self):
        """Initialize Ollama service with discovered endpoints"""
        endpoints = settings.discovered_services.ollama.get("endpoints", [])
        
        for endpoint in endpoints:
            self._clients[endpoint] = httpx.AsyncClient(
                base_url=endpoint,
                timeout=httpx.Timeout(30.0, connect=5.0)
            )
        
        # Set default endpoint
        if endpoints:
            self._default_endpoint = endpoints[0]
            logger.info(f"Ollama service initialized with {len(endpoints)} endpoints")
        else:
            logger.warning("No Ollama endpoints discovered")
    
    async def get_available_models(self, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available models from Ollama endpoint"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            return []
        
        # Check cache first
        if endpoint in self._model_cache:
            return self._model_cache[endpoint]
        
        try:
            client = self._clients.get(endpoint)
            if not client:
                client = httpx.AsyncClient(base_url=endpoint)
                self._clients[endpoint] = client
            
            response = await client.get("/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                self._model_cache[endpoint] = models
                return models
            else:
                logger.error(f"Failed to get models from {endpoint}: {response.status_code}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting models from {endpoint}: {e}")
            return []
    
    async def stream_chat(
        self,
        model: str,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        endpoint: Optional[str] = None,
        temperature: float = 0.7,
        project_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from Ollama"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            yield "Error: No Ollama endpoint available"
            return
        
        client = self._clients.get(endpoint)
        if not client:
            yield "Error: Ollama client not initialized"
            return
        
        # Build messages
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add context if provided
        if context:
            messages.extend(context)
        
        # Add user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            # Stream the response
            async with client.stream(
                "POST",
                "/api/chat",
                json=payload,
                timeout=httpx.Timeout(60.0, connect=5.0)
            ) as response:
                if response.status_code != 200:
                    yield f"Error: Ollama returned status {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data:
                                content = data["message"].get("content", "")
                                if content:
                                    yield content
                            
                            # Check if done
                            if data.get("done", False):
                                break
                        
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON: {line}")
                            continue
        
        except httpx.TimeoutException:
            yield "Error: Request timed out"
        except Exception as e:
            logger.error(f"Error in stream_chat: {e}")
            yield f"Error: {str(e)}"
    
    async def generate(
        self,
        model: str,
        prompt: str,
        endpoint: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate completion from Ollama"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            return "Error: No Ollama endpoint available"
        
        client = self._clients.get(endpoint)
        if not client:
            return "Error: Ollama client not initialized"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = await client.post("/api/generate", json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "")
            else:
                return f"Error: Ollama returned status {response.status_code}"
        
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            return f"Error: {str(e)}"
    
    async def pull_model(self, model_name: str, endpoint: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Pull a model from Ollama registry"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            yield "Error: No Ollama endpoint available"
            return
        
        client = self._clients.get(endpoint)
        if not client:
            yield "Error: Ollama client not initialized"
            return
        
        try:
            async with client.stream(
                "POST",
                "/api/pull",
                json={"name": model_name, "stream": True}
            ) as response:
                if response.status_code != 200:
                    yield f"Error: Failed to pull model - status {response.status_code}"
                    return
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            status = data.get("status", "")
                            if status:
                                yield status
                            
                            # Include progress if available
                            if "completed" in data and "total" in data:
                                progress = (data["completed"] / data["total"]) * 100
                                yield f"Progress: {progress:.1f}%"
                        
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            yield f"Error: {str(e)}"
    
    async def delete_model(self, model_name: str, endpoint: Optional[str] = None) -> bool:
        """Delete a model from Ollama"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            return False
        
        client = self._clients.get(endpoint)
        if not client:
            return False
        
        try:
            response = await client.delete("/api/delete", json={"name": model_name})
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting model: {e}")
            return False
    
    async def get_model_info(self, model_name: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about a model"""
        endpoint = endpoint or self._default_endpoint
        if not endpoint:
            return {}
        
        client = self._clients.get(endpoint)
        if not client:
            return {}
        
        try:
            response = await client.post("/api/show", json={"name": model_name})
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}
    
    def get_active_endpoints(self) -> List[str]:
        """Get list of active Ollama endpoints"""
        return list(self._clients.keys())
    
    def set_default_endpoint(self, endpoint: str):
        """Set the default Ollama endpoint"""
        if endpoint in self._clients:
            self._default_endpoint = endpoint
            logger.info(f"Default Ollama endpoint set to: {endpoint}")
        else:
            logger.error(f"Endpoint {endpoint} not found in active clients")
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self._clients.values():
            await client.aclose()
        self._clients.clear()
        self._model_cache.clear()