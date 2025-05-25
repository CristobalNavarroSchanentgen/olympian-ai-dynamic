"""Configuration settings for Olympian AI"""
import os
from typing import List, Dict, Any, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import yaml
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with divine configuration"""
    
    # Basic settings
    app_name: str = "Olympian AI Dynamic"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    server_host: str = Field(default="127.0.0.1", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    
    # API settings
    api_prefix: str = "/api"
    cors_origins: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:5173",
        env="CORS_ORIGINS"
    )
    
    # Ollama settings
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL"
    )
    ollama_timeout: int = Field(default=120, env="OLLAMA_TIMEOUT")
    ollama_endpoints: Union[str, List[str]] = Field(
        default="http://localhost:11434",
        env="OLLAMA_ENDPOINTS"
    )
    
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
    jwt_secret: str = Field(
        default="your-secret-key-here-change-in-production",
        env="JWT_SECRET"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=1440, env="JWT_EXPIRATION_MINUTES")
    
    # Service discovery
    service_discovery_enabled: bool = Field(
        default=True,
        env="SERVICE_DISCOVERY_ENABLED"
    )
    discovery_enabled: bool = Field(
        default=True,
        env="DISCOVERY_ENABLED"
    )
    service_scan_interval: int = Field(
        default=300,  # 5 minutes
        env="SERVICE_SCAN_INTERVAL"
    )
    discovery_scan_interval: int = Field(
        default=30,
        env="DISCOVERY_SCAN_INTERVAL"
    )
    
    # MCP settings
    mcp_enabled: bool = Field(default=True, env="MCP_ENABLED")
    mcp_servers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Data and Project settings
    data_directory: str = Field(default="data", env="DATA_DIR")
    projects_dir: str = Field(default="data/projects", env="PROJECTS_DIR")
    max_context_size: int = Field(default=100000, env="MAX_CONTEXT_SIZE")
    
    # Webhook settings
    webhook_timeout: int = Field(default=30, env="WEBHOOK_TIMEOUT")
    webhook_max_retries: int = Field(default=3, env="WEBHOOK_MAX_RETRIES")
    
    # External service integrations
    mattermost_url: Optional[str] = Field(default=None, env="MATTERMOST_URL")
    mattermost_token: Optional[str] = Field(default=None, env="MATTERMOST_TOKEN")
    discord_webhook_url: Optional[str] = Field(default=None, env="DISCORD_WEBHOOK_URL")
    
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
        extra = "ignore"  # Allow extra fields without validation errors
    
    @property
    def data_dir(self) -> Path:
        """Get data directory as Path object"""
        return Path(self.data_directory)
    
    @property
    def user_preferences(self):
        """Get user preferences - placeholder for now"""
        return {
            "preferred_models": [],
            "custom_endpoints": [],
            "disabled_services": [],
            "manual_overrides": {}
        }
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("ollama_endpoints", mode="before")
    @classmethod
    def parse_ollama_endpoints(cls, v):
        """Parse Ollama endpoints from string or list"""
        if isinstance(v, str):
            return [endpoint.strip() for endpoint in v.split(",")]
        return v
    
    @field_validator("mcp_servers", mode="before")
    @classmethod
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
    
    def save_config(self):
        """Save configuration - placeholder for now"""
        # This would typically save to a config file or database
        pass
    
    def get_ollama_models(self) -> List[str]:
        """Get list of preferred Ollama models"""
        return self.discovered_services.get("ollama", {}).get("models", [])
    
    def get_ollama_endpoints(self) -> List[str]:
        """Get list of Ollama endpoints"""
        if isinstance(self.ollama_endpoints, list):
            return self.ollama_endpoints
        return [self.ollama_base_url]
    
    def get_active_services(self) -> List[str]:
        """Get list of active services"""
        active = []
        if self.discovered_services.get("ollama"):
            active.append("ollama")
        if self.discovered_services.get("redis"):
            active.append("redis")
        if self.mcp_enabled:
            active.append("mcp")
        return active
    
    def add_cors_origin(self, origin: str):
        """Add a new CORS origin"""
        if isinstance(self.cors_origins, list):
            if origin not in self.cors_origins:
                self.cors_origins.append(origin)
        else:
            # Convert string to list and add
            origins = [o.strip() for o in self.cors_origins.split(",")]
            if origin not in origins:
                origins.append(origin)
                self.cors_origins = origins
    
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
    
    def get_effective_jwt_secret(self) -> str:
        """Get the JWT secret, preferring jwt_secret over jwt_secret_key"""
        return self.jwt_secret or self.jwt_secret_key
    
    def is_service_discovery_enabled(self) -> bool:
        """Check if service discovery is enabled (supports both field names)"""
        return self.service_discovery_enabled or self.discovery_enabled
    
    def get_effective_scan_interval(self) -> int:
        """Get the scan interval, preferring discovery_scan_interval if set"""
        if self.discovery_scan_interval != 30:  # If it's not the default
            return self.discovery_scan_interval
        return self.service_scan_interval


# Create global settings instance
settings = Settings()

# Load additional config from file
settings.load_config_file()

# Environment-specific adjustments
if settings.is_production():
    settings.debug = False
    # Add production-specific settings here
