"""Configuration settings for Olympian AI"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator, field_validator
import yaml
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with divine configuration"""
    
    # Basic settings
    app_name: str = "Olympian AI Dynamic"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API settings
    api_prefix: str = "/api"
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    ollama_timeout: int = Field(default=120, env="OLLAMA_TIMEOUT")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # Supabase settings (optional)
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    
    # Security settings
    jwt_secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        env="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, env="JWT_EXPIRATION_MINUTES")
    
    # Service discovery
    service_discovery_enabled: bool = Field(
        default=True,
        env="SERVICE_DISCOVERY_ENABLED"
    )
    service_scan_interval: int = Field(
        default=300,  # 5 minutes
        env="SERVICE_SCAN_INTERVAL"
    )
    
    # MCP settings
    mcp_enabled: bool = Field(default=True, env="MCP_ENABLED")
    mcp_servers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Project settings
    projects_dir: str = Field(default="data/projects", env="PROJECTS_DIR")
    max_context_size: int = Field(default=100000, env="MAX_CONTEXT_SIZE")
    
    # Webhook settings
    webhook_timeout: int = Field(default=30, env="WEBHOOK_TIMEOUT")
    webhook_max_retries: int = Field(default=3, env="WEBHOOK_MAX_RETRIES")
    
    # System settings
    max_upload_size: int = Field(
        default=100 * 1024 * 1024,  # 100MB
        env="MAX_UPLOAD_SIZE"
    )
    
    # Discovered services (runtime)
    discovered_services: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @field_validator("cors_origins", mode="before")
    @classmethod    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("mcp_servers", pre=True)
    def load_mcp_servers(cls, v):
        """Load MCP servers from config file if not provided"""
        if not v:
            config_path = Path("config.yaml")
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config_data = yaml.safe_load(f)
                        return config_data.get("mcp_servers", [])
                except Exception:
                    pass
        return v
    
    def load_config_file(self):
        """Load additional configuration from YAML file"""
        config_path = Path("config.yaml")
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config_data = yaml.safe_load(f)
                    
                    # Update settings with config file data
                    for key, value in config_data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    def get_ollama_models(self) -> List[str]:
        """Get list of preferred Ollama models"""
        return self.discovered_services.get("ollama", {}).get("models", [])
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    def get_redis_settings(self) -> Dict[str, Any]:
        """Get Redis connection settings"""
        return {
            "url": self.redis_url,
            "encoding": "utf-8",
            "decode_responses": True
        }


# Create global settings instance
settings = Settings()

# Load additional config from file
settings.load_config_file()

# Environment-specific adjustments
if settings.is_production():
    settings.debug = False
    # Add production-specific settings here
