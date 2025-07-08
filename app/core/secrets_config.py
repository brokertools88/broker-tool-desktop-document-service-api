"""
AWS Secrets Manager Configuration for InsureCove Document Service

This module provides configuration classes that integrate with AWS Secrets Manager
instead of environment variables for sensitive configuration.

Author: InsureCove Team
Date: July 8, 2025
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os
import logging
from enum import Enum

from app.services.secrets_service import get_secrets_manager, DocumentServiceSecretsManager
from app.core.exceptions import ConfigurationError


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageType(str, Enum):
    """Storage backend types"""
    LOCAL = "local"
    S3 = "s3"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SecretsBasedConfig:
    """
    Configuration class that loads sensitive settings from AWS Secrets Manager
    and non-sensitive settings from environment variables.
    """
    
    def __init__(self, environment: Optional[str] = None):
        """
        Initialize configuration with AWS Secrets Manager integration.
        
        Args:
            environment: Environment name (development, staging, production)
                        If None, will be read from ENVIRONMENT env var
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine environment
        self.environment = environment or os.getenv("ENVIRONMENT", "production")
        self._aws_region = os.getenv("AWS_REGION", "ap-east-1")
        
        # Initialize secrets manager
        self.secrets_manager = get_secrets_manager(self.environment, self._aws_region)
        
        # Cache for loaded configurations
        self._config_cache: Dict[str, Any] = {}
        
        self.logger.info(f"Initialized SecretsBasedConfig for {self.environment} environment")
    
    
    # ============= APPLICATION SETTINGS =============
    @property
    def app_name(self) -> str:
        return "InsureCove Document Service"
    
    @property
    def app_version(self) -> str:
        return "1.0.0"
    
    @property
    def environment_enum(self) -> Environment:
        try:
            return Environment(self.environment)
        except ValueError:
            return Environment.PRODUCTION
    
    @property
    def debug(self) -> bool:
        return self.environment in ["development", "testing"]
    
    @property
    def log_level(self) -> LogLevel:
        # Try to get from monitoring config, fallback to env var
        try:
            monitoring_config = self._get_monitoring_config()
            level = monitoring_config.get("log_level", "INFO")
            return LogLevel(level)
        except:
            return LogLevel(os.getenv("LOG_LEVEL", "INFO"))
    
    
    # ============= SERVER SETTINGS =============
    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")
    
    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))
    
    @property
    def workers(self) -> int:
        return int(os.getenv("WORKERS", "1"))
    
    @property
    def reload(self) -> bool:
        return self.debug
    
    
    # ============= SECURITY SETTINGS =============
    @property
    def secret_key(self) -> str:
        """Get application secret key from AWS Secrets Manager"""
        try:
            jwt_config = self._get_jwt_config()
            return jwt_config.get("secret_key", "dev-secret-key-change-in-production")
        except Exception as e:
            self.logger.warning(f"Failed to get secret key from AWS: {e}")
            return os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    @property
    def allowed_hosts(self) -> List[str]:
        return os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    @property
    def cors_origins(self) -> List[str]:
        return os.getenv("CORS_ORIGINS", "*").split(",")
    
    @property
    def cors_credentials(self) -> bool:
        return os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    
    
    # ============= AUTHENTICATION SERVICE =============
    @property
    def auth_service_url(self) -> str:
        """Get auth service URL from AWS Secrets Manager"""
        try:
            auth_config = self._get_auth_service_config()
            return auth_config["service_url"]
        except Exception as e:
            self.logger.warning(f"Failed to get auth service URL from AWS: {e}")
            return os.getenv("AUTH_SERVICE_URL", "http://localhost:8000")
    
    @property
    def auth_service_api_key(self) -> Optional[str]:
        """Get auth service API key from AWS Secrets Manager"""
        try:
            auth_config = self._get_auth_service_config()
            return auth_config.get("api_key")
        except Exception as e:
            self.logger.warning(f"Failed to get auth service API key from AWS: {e}")
            return None
    
    @property
    def auth_service_timeout(self) -> int:
        return int(os.getenv("AUTH_SERVICE_TIMEOUT", "30"))
    
    
    # ============= DATABASE SETTINGS =============
    @property
    def database_url(self) -> Optional[str]:
        """Get database URL from AWS Secrets Manager"""
        try:
            db_config = self._get_database_config()
            return db_config.get("connection_string")
        except Exception as e:
            self.logger.info(f"Database configuration not available: {e}")
            return None
    
    @property
    def database_pool_size(self) -> int:
        return int(os.getenv("DATABASE_POOL_SIZE", "20"))
    
    
    # ============= AWS CONFIGURATION =============
    @property
    def aws_region(self) -> str:
        return self._aws_region
    
    @property
    def aws_s3_bucket(self) -> str:
        """Get S3 bucket name from AWS Secrets Manager"""
        try:
            storage_config = self._get_storage_config()
            return storage_config["bucket_name"]
        except Exception as e:
            self.logger.warning(f"Failed to get S3 bucket from AWS: {e}")
            return os.getenv("AWS_S3_BUCKET", "insurecove-documents")
    
    @property
    def aws_s3_prefix(self) -> str:
        """Get S3 prefix from AWS Secrets Manager"""
        try:
            storage_config = self._get_storage_config()
            return storage_config.get("prefix", "documents/")
        except Exception as e:
            return os.getenv("AWS_S3_PREFIX", "documents/")
    
    
    # ============= STORAGE CONFIGURATION =============
    @property
    def storage_type(self) -> StorageType:
        storage_type_str = os.getenv("STORAGE_TYPE", "s3" if self.environment == "production" else "local")
        try:
            return StorageType(storage_type_str)
        except ValueError:
            return StorageType.S3
    
    @property
    def local_storage_path(self) -> str:
        return os.getenv("LOCAL_STORAGE_PATH", "./storage")
    
    @property
    def max_file_size_mb(self) -> int:
        try:
            storage_config = self._get_storage_config()
            return storage_config.get("upload_limits", {}).get("max_file_size_mb", 50)
        except Exception:
            return int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    @property
    def allowed_file_types(self) -> List[str]:
        try:
            storage_config = self._get_storage_config()
            return storage_config.get("upload_limits", {}).get("allowed_file_types", 
                                    ["pdf", "jpeg", "jpg", "png", "tiff", "tif"])
        except Exception:
            return os.getenv("ALLOWED_FILE_TYPES", "pdf,jpeg,jpg,png,tiff,tif").split(",")
    
    
    # ============= OCR CONFIGURATION =============
    @property
    def mistral_api_key(self) -> str:
        """Get Mistral AI API key from AWS Secrets Manager"""
        try:
            mistral_config = self._get_mistral_ai_config()
            return mistral_config["api_key"]
        except Exception as e:
            self.logger.error(f"Failed to get Mistral API key from AWS: {e}")
            # Fallback to env var for development
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ConfigurationError("Mistral AI API key not available in AWS Secrets Manager or environment variables")
            return api_key
    
    @property
    def mistral_api_url(self) -> str:
        """Get Mistral AI API URL from AWS Secrets Manager"""
        try:
            mistral_config = self._get_mistral_ai_config()
            return mistral_config.get("api_endpoint", "https://api.mistral.ai/v1")
        except Exception:
            return os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1")
    
    @property
    def mistral_model(self) -> str:
        """Get Mistral AI model name from AWS Secrets Manager"""
        try:
            mistral_config = self._get_mistral_ai_config()
            return mistral_config.get("model_config", {}).get("model", "mistral-ocr-latest")
        except Exception:
            return os.getenv("MISTRAL_MODEL", "mistral-ocr-latest")
    
    @property
    def ocr_timeout_seconds(self) -> int:
        return int(os.getenv("OCR_TIMEOUT_SECONDS", "300"))
    
    
    # ============= JWT CONFIGURATION =============
    @property
    def jwt_public_key(self) -> str:
        """Get JWT public key from AWS Secrets Manager"""
        try:
            jwt_config = self._get_jwt_config()
            return jwt_config["public_key"]
        except Exception as e:
            self.logger.error(f"Failed to get JWT public key from AWS: {e}")
            raise ConfigurationError("JWT public key not available in AWS Secrets Manager")
    
    @property
    def jwt_algorithm(self) -> str:
        """Get JWT algorithm from AWS Secrets Manager"""
        try:
            jwt_config = self._get_jwt_config()
            return jwt_config.get("algorithm", "RS256")
        except Exception:
            return "RS256"
    
    @property
    def jwt_issuer(self) -> Optional[str]:
        """Get JWT issuer from AWS Secrets Manager"""
        try:
            jwt_config = self._get_jwt_config()
            return jwt_config.get("issuer")
        except Exception:
            return None
    
    @property
    def jwt_audience(self) -> Optional[str]:
        """Get JWT audience from AWS Secrets Manager"""
        try:
            jwt_config = self._get_jwt_config()
            return jwt_config.get("audience")
        except Exception:
            return None
    
    
    # ============= RATE LIMITING =============
    @property
    def rate_limit_requests_per_minute(self) -> int:
        return int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
    
    @property
    def upload_rate_limit_per_hour(self) -> int:
        return int(os.getenv("UPLOAD_RATE_LIMIT_PER_HOUR", "1000"))
    
    @property
    def ocr_rate_limit_per_hour(self) -> int:
        return int(os.getenv("OCR_RATE_LIMIT_PER_HOUR", "500"))
    
    
    # ============= MONITORING CONFIGURATION =============
    @property
    def enable_metrics(self) -> bool:
        return os.getenv("ENABLE_METRICS", "true").lower() == "true"
    
    @property
    def metrics_port(self) -> int:
        return int(os.getenv("METRICS_PORT", "9090"))
    
    @property
    def health_check_timeout(self) -> int:
        return int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
    
    @property
    def sentry_dsn(self) -> Optional[str]:
        """Get Sentry DSN from AWS Secrets Manager"""
        try:
            monitoring_config = self._get_monitoring_config()
            return monitoring_config.get("sentry_dsn")
        except Exception:
            return os.getenv("SENTRY_DSN")
    
    
    # ============= FEATURE FLAGS =============
    @property
    def enable_ocr_auto_processing(self) -> bool:
        return os.getenv("ENABLE_OCR_AUTO_PROCESSING", "true").lower() == "true"
    
    @property
    def enable_thumbnail_generation(self) -> bool:
        return os.getenv("ENABLE_THUMBNAIL_GENERATION", "true").lower() == "true"
    
    @property
    def enable_batch_processing(self) -> bool:
        return os.getenv("ENABLE_BATCH_PROCESSING", "true").lower() == "true"
    
    
    # ============= UTILITY PROPERTIES =============
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"
    
    
    # ============= PRIVATE HELPER METHODS =============
    def _get_mistral_ai_config(self) -> Dict[str, Any]:
        """Get Mistral AI configuration from cache or AWS Secrets Manager"""
        if "mistral_ai" not in self._config_cache:
            import asyncio
            self._config_cache["mistral_ai"] = asyncio.run(
                self.secrets_manager.get_mistral_ai_config()
            )
        return self._config_cache["mistral_ai"]
    
    def _get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration from cache or AWS Secrets Manager"""
        if "storage" not in self._config_cache:
            import asyncio
            self._config_cache["storage"] = asyncio.run(
                self.secrets_manager.get_storage_config()
            )
        return self._config_cache["storage"]
    
    def _get_auth_service_config(self) -> Dict[str, Any]:
        """Get auth service configuration from cache or AWS Secrets Manager"""
        if "auth_service" not in self._config_cache:
            import asyncio
            self._config_cache["auth_service"] = asyncio.run(
                self.secrets_manager.get_auth_service_config()
            )
        return self._config_cache["auth_service"]
    
    def _get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from cache or AWS Secrets Manager"""
        if "database" not in self._config_cache:
            import asyncio
            self._config_cache["database"] = asyncio.run(
                self.secrets_manager.get_database_config()
            )
        return self._config_cache["database"]
    
    def _get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration from cache or AWS Secrets Manager"""
        if "jwt" not in self._config_cache:
            import asyncio
            self._config_cache["jwt"] = asyncio.run(
                self.secrets_manager.get_jwt_config()
            )
        return self._config_cache["jwt"]
    
    def _get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration from cache or AWS Secrets Manager"""
        if "monitoring" not in self._config_cache:
            import asyncio
            self._config_cache["monitoring"] = asyncio.run(
                self.secrets_manager.get_monitoring_config()
            )
        return self._config_cache["monitoring"]
    
    
    def clear_config_cache(self) -> None:
        """Clear the configuration cache to force reload from AWS Secrets Manager"""
        self._config_cache.clear()
        self.logger.info("Configuration cache cleared")
    
    
    async def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate all configuration settings.
        
        Returns:
            Dict mapping configuration sections to validation status
        """
        validation_results = {}
        
        # Validate secrets-based configurations
        try:
            await self.secrets_manager.get_mistral_ai_config()
            validation_results["mistral_ai"] = True
        except Exception as e:
            validation_results["mistral_ai"] = False
            self.logger.error(f"Mistral AI config validation failed: {e}")
        
        try:
            await self.secrets_manager.get_storage_config()
            validation_results["storage"] = True
        except Exception as e:
            validation_results["storage"] = False
            self.logger.error(f"Storage config validation failed: {e}")
        
        try:
            await self.secrets_manager.get_auth_service_config()
            validation_results["auth_service"] = True
        except Exception as e:
            validation_results["auth_service"] = False
            self.logger.error(f"Auth service config validation failed: {e}")
        
        try:
            await self.secrets_manager.get_jwt_config()
            validation_results["jwt"] = True
        except Exception as e:
            validation_results["jwt"] = False
            self.logger.error(f"JWT config validation failed: {e}")
        
        # Add environment-based validations
        validation_results["environment"] = self.environment in ["development", "testing", "staging", "production"]
        validation_results["aws_region"] = bool(self.aws_region)
        
        return validation_results


# Global configuration instance
_config: Optional[SecretsBasedConfig] = None


def get_config(environment: Optional[str] = None) -> SecretsBasedConfig:
    """
    Get the global configuration instance.
    
    Args:
        environment: Environment name (only used for first initialization)
        
    Returns:
        SecretsBasedConfig: Global configuration instance
    """
    global _config
    
    if _config is None:
        _config = SecretsBasedConfig(environment)
    
    return _config


async def initialize_config(environment: Optional[str] = None) -> SecretsBasedConfig:
    """
    Initialize and validate the global configuration.
    
    Args:
        environment: Environment name
        
    Returns:
        SecretsBasedConfig: Initialized configuration instance
        
    Raises:
        ConfigurationError: If configuration validation fails
    """
    config = get_config(environment)
    
    # Validate configuration
    validation_results = await config.validate_configuration()
    
    failed_sections = [section for section, status in validation_results.items() if not status]
    if failed_sections:
        raise ConfigurationError(f"Configuration validation failed for sections: {failed_sections}")
    
    logging.getLogger(__name__).info("Configuration initialized and validated successfully")
    return config
