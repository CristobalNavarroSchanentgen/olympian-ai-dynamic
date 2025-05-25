"""Service Discovery Engine for Olympian AI

Automatically discovers and monitors available services like Ollama, MCP servers,
and other AI/ML services on the network.
"""
import asyncio
import httpx
import psutil
import platform
import socket
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import json

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class ServiceDiscoveryEngine:
    """Divine service discovery - finding mortal services in the digital realm"""
    
    def __init__(self):
        self._running = False
        self._scan_task = None
        self._discovered_services = {}
        self._last_scan = None
        self._http_client = None
        
    async def start(self):
        """Start the discovery engine"""
        self._running = True
        self._http_client = httpx.AsyncClient(timeout=10.0)
        logger.info("🔍 Service Discovery Engine started")
        
    def stop(self):
        """Stop the discovery engine"""
        self._running = False
        if self._scan_task:
            self._scan_task.cancel()
        if self._http_client:
            asyncio.create_task(self._http_client.aclose())
        logger.info("Service Discovery Engine stopped")
    
    async def discover_ollama_instances(self) -> Dict[str, Any]:
        """Discover Ollama instances on the network"""
        logger.info("🔍 Scanning for Ollama instances...")
        
        ollama_services = {
            "endpoints": [],
            "models": [],
            "capabilities": {}
        }
        
        # Common Ollama ports and hosts to check
        hosts_to_check = [
            "localhost",
            "127.0.0.1",
            "host.docker.internal",  # Docker host
            "ollama",  # Docker service name
        ]
        
        ports_to_check = [11434, 11435, 11436]  # Default and alternative ports
        
        if not self._http_client:
            logger.error("HTTP client not initialized. Call start() first.")
            return ollama_services
        
        for host in hosts_to_check:
            for port in ports_to_check:
                url = f"http://{host}:{port}"
                try:
                    logger.debug(f"Checking Ollama at {url}")
                    
                    # Check if Ollama is running
                    response = await self._http_client.get(f"{url}/api/tags", timeout=5.0)
                    if response.status_code == 200:
                        ollama_services["endpoints"].append(url)
                        
                        # Get available models
                        data = response.json()
                        if "models" in data:
                            for model in data["models"]:
                                if model not in ollama_services["models"]:
                                    ollama_services["models"].append(model)
                        
                        # Check capabilities
                        ollama_services["capabilities"] = {
                            "embeddings": True,
                            "chat": True,
                            "completion": True
                        }
                        
                        logger.info(f"✅ Found Ollama instance at {url} with {len(data.get('models', []))} models")
                        
                        # Only check first working port per host to avoid duplicates
                        break
                        
                except httpx.ConnectError:
                    logger.debug(f"❌ Connection refused at {url}")
                    continue
                except httpx.TimeoutException:
                    logger.debug(f"⏰ Timeout connecting to {url}")
                    continue
                except Exception as e:
                    logger.debug(f"❌ Error connecting to {url}: {e}")
                    continue
        
        logger.info(f"🎯 Ollama discovery complete - found {len(ollama_services['endpoints'])} instances")
        return ollama_services
    
    async def scan_system_resources(self) -> Dict[str, Any]:
        """Scan system resources and capabilities"""
        logger.debug("📊 Scanning system resources...")
        
        resources = {
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {},
            "gpu": {"available": False, "devices": []},
            "network": {
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname())
            },
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        }
        
        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                resources["disk"][partition.device] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except:
                continue
        
        # GPU information
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                resources["gpu"]["available"] = len(gpus) > 0
                resources["gpu"]["devices"] = [
                    {
                        "id": gpu.id,
                        "name": gpu.name,
                        "memory_total": gpu.memoryTotal,
                        "memory_used": gpu.memoryUsed,
                        "memory_free": gpu.memoryFree,
                        "temperature": gpu.temperature,
                        "load": gpu.load
                    }
                    for gpu in gpus
                ]
                logger.info(f"🎮 Found {len(gpus)} GPU(s)")
            except:
                pass
        
        return resources
    
    async def discover_mcp_servers(self) -> List[Dict[str, Any]]:
        """Discover Model Context Protocol servers"""
        logger.debug("🔌 Scanning for MCP servers...")
        mcp_servers = []
        
        # Check for known MCP server patterns
        # This is a placeholder - actual implementation would scan for MCP servers
        
        return mcp_servers
    
    async def discover_docker_services(self) -> Dict[str, Any]:
        """Discover services running in Docker containers"""
        logger.debug("🐳 Scanning Docker services...")
        docker_services = {
            "containers": [],
            "images": []
        }
        
        try:
            import docker
            client = docker.from_env()
            
            # List running containers
            for container in client.containers.list():
                docker_services["containers"].append({
                    "id": container.short_id,
                    "name": container.name,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "status": container.status,
                    "ports": container.ports
                })
            
            # List available images
            for image in client.images.list():
                if image.tags:
                    docker_services["images"].append({
                        "id": image.short_id,
                        "tags": image.tags,
                        "size": image.attrs.get("Size", 0)
                    })
                    
            logger.info(f"🐳 Found {len(docker_services['containers'])} containers, {len(docker_services['images'])} images")
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")
        
        return docker_services
    
    async def full_scan(self) -> Dict[str, Any]:
        """Perform a full service discovery scan"""
        logger.info("🔍 Starting full service discovery scan...")
        
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "system": await self.scan_system_resources(),
                "services": {
                    "ollama": await self.discover_ollama_instances(),
                    "mcp": await self.discover_mcp_servers(),
                    "docker": await self.discover_docker_services()
                }
            }
            
            self._discovered_services = results
            self._last_scan = datetime.now()
            
            # Log summary
            ollama_count = len(results["services"]["ollama"]["endpoints"])
            mcp_count = len(results["services"]["mcp"])
            docker_count = len(results["services"]["docker"]["containers"])
            
            logger.info(f"✅ Service discovery scan complete:")
            logger.info(f"   📡 Ollama instances: {ollama_count}")
            logger.info(f"   🔌 MCP servers: {mcp_count}")
            logger.info(f"   🐳 Docker containers: {docker_count}")
            
            return results
        except Exception as e:
            logger.error(f"❌ Error during full scan: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "system": {},
                "services": {"ollama": {"endpoints": [], "models": []}, "mcp": [], "docker": {"containers": []}}
            }
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Check health status of discovered services"""
        health_status = {}
        
        if not self._http_client:
            logger.warning("HTTP client not available for health checks")
            return health_status
        
        # Check Ollama instances
        ollama_endpoints = self._discovered_services.get("services", {}).get("ollama", {}).get("endpoints", [])
        for endpoint in ollama_endpoints:
            try:
                response = await self._http_client.get(f"{endpoint}/api/tags", timeout=5.0)
                health_status[f"ollama_{endpoint}"] = response.status_code == 200
            except:
                health_status[f"ollama_{endpoint}"] = False
        
        # System health
        try:
            health_status["system"] = {
                "cpu_ok": psutil.cpu_percent() < 90,
                "memory_ok": psutil.virtual_memory().percent < 90,
                "disk_ok": all(usage.percent < 90 for usage in [psutil.disk_usage(p.mountpoint) for p in psutil.disk_partitions() if p.mountpoint])
            }
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            health_status["system"] = {"error": str(e)}
        
        return health_status
    
    def get_discovered_services(self) -> Dict[str, Any]:
        """Get the currently discovered services"""
        return self._discovered_services
    
    async def _check_ollama_endpoint(self, url: str) -> bool:
        """Check if an Ollama endpoint is accessible"""
        if not self._http_client:
            return False
            
        try:
            response = await self._http_client.get(f"{url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except:
            return False


# Global discovery engine instance
discovery_engine = ServiceDiscoveryEngine()
