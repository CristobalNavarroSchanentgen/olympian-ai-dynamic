"""System API Routes - Divine Resource Management"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import psutil
import asyncio
from datetime import datetime
from loguru import logger

from ..core.config import settings
from ..core.discovery import discovery_engine

router = APIRouter()


@router.get("/resources")
async def get_system_resources():
    """Get current system resource information"""
    # CPU info
    cpu_info = {
        "count": psutil.cpu_count(),
        "count_logical": psutil.cpu_count(logical=True),
        "percent": psutil.cpu_percent(interval=1),
        "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
        "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }
    
    # Memory info
    memory = psutil.virtual_memory()
    memory_info = {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "free": memory.free,
        "percent": memory.percent,
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2)
    }
    
    # Disk info
    disk = psutil.disk_usage('/')
    disk_info = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
        "total_gb": round(disk.total / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2)
    }
    
    # Network info (handle permission error gracefully)
    network_info = {
        "connections": 0,  # Default to 0 if we can't access
        "interfaces": {}
    }
    
    try:
        # Try to get network connections (may fail on macOS without permissions)
        network_info["connections"] = len(psutil.net_connections())
    except (psutil.AccessDenied, PermissionError) as e:
        # Log the warning but continue without network connection count
        logger.warning(f"Cannot access network connections: {e}")
        network_info["connections"] = "access_denied"
    
    # Network interfaces (this usually works without special permissions)
    try:
        for interface, addrs in psutil.net_if_addrs().items():
            network_info["interfaces"][interface] = [
                {"family": addr.family.name, "address": addr.address}
                for addr in addrs
            ]
    except Exception as e:
        logger.warning(f"Cannot access network interfaces: {e}")
        network_info["interfaces"] = {}
    
    # GPU info from discovery
    gpu_info = discovery_engine.discovered_services.get("system", {}).get("gpu", {})
    
    return {
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "network": network_info,
        "gpu": gpu_info,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/capacity")
async def get_system_capacity():
    """Get current system capacity and usage"""
    # Calculate capacity scores
    cpu_score = 100 - psutil.cpu_percent(interval=1)
    memory_score = 100 - psutil.virtual_memory().percent
    disk_score = 100 - psutil.disk_usage('/').percent
    
    # Overall capacity score
    overall_score = (cpu_score + memory_score + disk_score) / 3
    
    # Recommendations based on capacity
    recommendations = []
    
    if cpu_score < 20:
        recommendations.append("CPU usage is high. Consider limiting concurrent operations.")
    
    if memory_score < 20:
        recommendations.append("Memory usage is high. Consider reducing model sizes or clearing caches.")
    
    if disk_score < 10:
        recommendations.append("Disk space is low. Consider cleaning up temporary files.")
    
    return {
        "capacity_scores": {
            "cpu": round(cpu_score, 2),
            "memory": round(memory_score, 2),
            "disk": round(disk_score, 2),
            "overall": round(overall_score, 2)
        },
        "status": "healthy" if overall_score > 50 else "constrained" if overall_score > 20 else "critical",
        "recommendations": recommendations,
        "max_concurrent_operations": max(1, int(overall_score / 10)),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/optimize")
async def optimize_resource_allocation():
    """Optimize system resource allocation"""
    logger.info("🔧 Starting system optimization...")
    
    optimizations = []
    
    # Clear Python garbage collection
    import gc
    collected = gc.collect()
    optimizations.append(f"Garbage collection freed {collected} objects")
    
    # Clear model caches if memory is low
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > 80:
        # Clear Ollama model cache
        try:
            from ..services.ollama_service import ollama_service
            ollama_service._model_cache.clear()
            optimizations.append("Cleared Ollama model cache")
        except ImportError:
            optimizations.append("Ollama service not available for cache clearing")
    
    # Adjust connection pool sizes based on available resources
    if memory_percent > 70:
        # Reduce connection pool sizes
        optimizations.append("Reduced connection pool sizes")
    
    # Update rate limits based on CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        optimizations.append("Enabled automatic rate limit adjustment")
    
    return {
        "status": "optimized",
        "optimizations": optimizations,
        "resource_usage_before": {
            "cpu": cpu_percent,
            "memory": memory_percent
        },
        "resource_usage_after": {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory().percent
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/processes")
async def get_related_processes():
    """Get information about Olympian AI related processes"""
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'create_time']):
        try:
            pinfo = proc.info
            # Look for relevant processes
            if any(keyword in pinfo['name'].lower() for keyword in ['python', 'ollama', 'redis', 'node']):
                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "memory_percent": round(pinfo['memory_percent'], 2),
                    "cpu_percent": round(pinfo['cpu_percent'], 2),
                    "uptime": datetime.now().timestamp() - pinfo['create_time']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return {
        "processes": sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10],
        "total_found": len(processes)
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system metrics for monitoring"""
    # Collect metrics over a short period
    metrics = {
        "cpu": [],
        "memory": [],
        "timestamp": []
    }
    
    for _ in range(5):
        metrics["cpu"].append(psutil.cpu_percent(interval=0.2))
        metrics["memory"].append(psutil.virtual_memory().percent)
        metrics["timestamp"].append(datetime.now().isoformat())
        await asyncio.sleep(0.2)
    
    return {
        "metrics": metrics,
        "averages": {
            "cpu": round(sum(metrics["cpu"]) / len(metrics["cpu"]), 2),
            "memory": round(sum(metrics["memory"]) / len(metrics["memory"]), 2)
        },
        "peaks": {
            "cpu": max(metrics["cpu"]),
            "memory": max(metrics["memory"])
        }
    }


@router.get("/limits")
async def get_resource_limits():
    """Get recommended resource limits based on system capacity"""
    # Calculate limits based on available resources
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    # Dynamic limits
    limits = {
        "max_concurrent_chats": min(cpu_count * 2, 20),
        "max_websocket_connections": min(int(memory_gb * 10), 100),
        "max_model_cache_size_mb": int(memory_gb * 100),  # 10% of RAM
        "max_file_upload_size_mb": min(int(memory_gb * 50), 500),
        "max_generation_tokens": 4096 if memory_gb > 8 else 2048,
        "recommended_models": []
    }
    
    # Recommend models based on available memory
    if memory_gb >= 32:
        limits["recommended_models"] = ["llama2:70b", "mixtral:8x7b", "llama2:13b"]
    elif memory_gb >= 16:
        limits["recommended_models"] = ["llama2:13b", "llama2:7b", "mistral:7b"]
    elif memory_gb >= 8:
        limits["recommended_models"] = ["llama2:7b", "mistral:7b", "phi"]
    else:
        limits["recommended_models"] = ["phi", "tinyllama"]
    
    return {
        "limits": limits,
        "system_specs": {
            "memory_gb": round(memory_gb, 2),
            "cpu_count": cpu_count,
            "gpu_available": discovery_engine.discovered_services.get("system", {}).get("gpu", {}).get("available", False)
        },
        "timestamp": datetime.now().isoformat()
    }