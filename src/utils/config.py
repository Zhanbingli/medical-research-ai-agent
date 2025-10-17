"""
Configuration management module with validation.

Provides centralized configuration with environment variable validation
and default values.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIProviderConfig:
    """Configuration for AI providers."""
    anthropic_api_key: Optional[str] = None
    kimi_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    default_provider: str = "claude"


@dataclass
class PubMedConfig:
    """Configuration for PubMed client."""
    email: str = "user@example.com"
    request_delay: float = 0.34  # 3 requests per second


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    cache_dir: str = "./cache"
    expiry_days: int = 7
    size_limit_mb: int = 500


@dataclass
class CostConfig:
    """Configuration for cost tracking."""
    enabled: bool = True
    daily_limit: float = 10.0
    monthly_limit: float = 100.0
    storage_path: str = "./cache/usage_stats.json"


@dataclass
class LogConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


@dataclass
class AppConfig:
    """Main application configuration."""
    ai: AIProviderConfig
    pubmed: PubMedConfig
    cache: CacheConfig
    cost: CostConfig
    log: LogConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Load configuration from environment variables.

        Returns:
            AppConfig instance with validated settings
        """
        # Load .env file
        load_dotenv()

        # AI Provider Config
        ai_config = AIProviderConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            kimi_api_key=os.getenv("KIMI_API_KEY"),
            qwen_api_key=os.getenv("QWEN_API_KEY"),
            default_provider=os.getenv("DEFAULT_AI_PROVIDER", "claude")
        )

        # PubMed Config
        pubmed_config = PubMedConfig(
            email=os.getenv("PUBMED_EMAIL", "user@example.com"),
            request_delay=float(os.getenv("PUBMED_REQUEST_DELAY", "0.34"))
        )

        # Cache Config
        cache_config = CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_dir=os.getenv("CACHE_DIR", "./cache"),
            expiry_days=int(os.getenv("CACHE_EXPIRY_DAYS", "7")),
            size_limit_mb=int(os.getenv("CACHE_SIZE_LIMIT_MB", "500"))
        )

        # Cost Config
        cost_config = CostConfig(
            enabled=os.getenv("COST_TRACKING_ENABLED", "true").lower() == "true",
            daily_limit=float(os.getenv("COST_DAILY_LIMIT", "10.0")),
            monthly_limit=float(os.getenv("COST_MONTHLY_LIMIT", "100.0")),
            storage_path=os.getenv("COST_STORAGE_PATH", "./cache/usage_stats.json")
        )

        # Log Config
        log_config = LogConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file=os.getenv("LOG_FILE")
        )

        return cls(
            ai=ai_config,
            pubmed=pubmed_config,
            cache=cache_config,
            cost=cost_config,
            log=log_config
        )

    def validate(self) -> Dict[str, Any]:
        """
        Validate configuration and return validation results.

        Returns:
            Dictionary with validation results and warnings
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Check if at least one AI provider is configured
        has_ai_provider = any([
            self.ai.anthropic_api_key,
            self.ai.kimi_api_key,
            self.ai.qwen_api_key
        ])

        if not has_ai_provider:
            results["valid"] = False
            results["errors"].append(
                "No AI provider API key configured. Set at least one: "
                "ANTHROPIC_API_KEY, KIMI_API_KEY, or QWEN_API_KEY"
            )

        # Validate default provider
        available_providers = []
        if self.ai.anthropic_api_key:
            available_providers.append("claude")
        if self.ai.kimi_api_key:
            available_providers.append("kimi")
        if self.ai.qwen_api_key:
            available_providers.append("qwen")

        if self.ai.default_provider not in available_providers:
            if available_providers:
                results["warnings"].append(
                    f"Default provider '{self.ai.default_provider}' not available. "
                    f"Will use: {available_providers[0]}"
                )
            else:
                results["errors"].append("No AI providers available")
                results["valid"] = False

        # Check PubMed email
        if self.pubmed.email == "user@example.com":
            results["warnings"].append(
                "Using default PubMed email. Set PUBMED_EMAIL for better rate limits."
            )

        # Check cost limits
        if self.cost.daily_limit > self.cost.monthly_limit:
            results["warnings"].append(
                "Daily cost limit exceeds monthly limit. This may cause issues."
            )

        # Check cache directory
        try:
            os.makedirs(self.cache.cache_dir, exist_ok=True)
        except Exception as e:
            results["errors"].append(f"Cannot create cache directory: {e}")
            results["valid"] = False

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (for display)."""
        return {
            "ai": {
                "has_anthropic_key": bool(self.ai.anthropic_api_key),
                "has_kimi_key": bool(self.ai.kimi_api_key),
                "has_qwen_key": bool(self.ai.qwen_api_key),
                "default_provider": self.ai.default_provider
            },
            "pubmed": {
                "email": self.pubmed.email,
                "request_delay": self.pubmed.request_delay
            },
            "cache": {
                "enabled": self.cache.enabled,
                "cache_dir": self.cache.cache_dir,
                "expiry_days": self.cache.expiry_days,
                "size_limit_mb": self.cache.size_limit_mb
            },
            "cost": {
                "enabled": self.cost.enabled,
                "daily_limit": self.cost.daily_limit,
                "monthly_limit": self.cost.monthly_limit
            },
            "log": {
                "level": self.log.level,
                "file": self.log.file
            }
        }


# Global configuration instance
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get or create global configuration instance.

    Returns:
        AppConfig instance
    """
    global _config

    if _config is None:
        _config = AppConfig.from_env()

        # Validate configuration
        validation = _config.validate()

        if not validation["valid"]:
            for error in validation["errors"]:
                logger.error(f"Configuration error: {error}")
            raise ValueError("Invalid configuration. Check logs for details.")

        for warning in validation["warnings"]:
            logger.warning(f"Configuration warning: {warning}")

        logger.info("Configuration loaded and validated successfully")

    return _config


# Example usage
if __name__ == "__main__":
    config = get_config()

    print("Configuration:")
    import json
    print(json.dumps(config.to_dict(), indent=2))

    validation = config.validate()
    print(f"\nValidation: {'✓ Valid' if validation['valid'] else '✗ Invalid'}")

    if validation["errors"]:
        print("\nErrors:")
        for error in validation["errors"]:
            print(f"  - {error}")

    if validation["warnings"]:
        print("\nWarnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
