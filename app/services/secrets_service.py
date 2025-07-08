"""
AWS Secrets Manager Service for InsureCove Document Service

This service provides centralized secret management for the document service,
integrating AWS Secrets Manager with the application's configuration system.

The service handles:
- Application secrets (API keys, database credentials, JWT secrets)
- Configuration secrets (service endpoints, third-party API keys)
- Service-specific secrets (Mistral AI API key, storage credentials)
- Secret caching and refresh logic
- Error handling and fallback strategies

Author: InsureCove Team
Date: July 8, 2025
"""

from typing import Dict, Any, Optional, Union
import logging
from datetime import datetime, timedelta
from functools import lru_cache
import asyncio

from app.utils.aws_secrets import AWSSecretsManager, AWSSecretsConfig, SecretValue
from app.core.exceptions import ConfigurationError


class DocumentServiceSecretsManager:
    """
    Centralized secrets management for the document service.
    
    This service provides a unified interface for retrieving and managing
    all secrets required by the document service, including:
    - Mistral AI API credentials
    - AWS S3 storage credentials
    - External auth service credentials
    - Database connection strings
    - JWT signing keys
    """
    
    def __init__(self, environment: str = "production", aws_region: str = "ap-east-1"):
        """
        Initialize the secrets manager.
        
        Args:
            environment: Environment name (development, staging, production)
            aws_region: AWS region for Secrets Manager
        """
        self.logger = logging.getLogger(__name__)
        self.environment = environment
        
        # Initialize AWS Secrets Manager with environment support
        aws_config = AWSSecretsConfig(
            aws_region=aws_region,
            secret_prefix="insurecove",
            environment=environment
        )
        self.secrets_manager = AWSSecretsManager(aws_config)
        
        # Cache for secrets with TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        self.logger.info(f"Initialized DocumentServiceSecretsManager for {environment} environment")
    
    
    async def get_mistral_ai_config(self) -> Dict[str, Any]:
        """
        Get Mistral AI API configuration.
        
        Returns:
            Dict containing:
            - api_key: Mistral AI API key
            - api_endpoint: API endpoint URL
            - model_config: Model configuration parameters
            - rate_limits: API rate limiting configuration
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "mistral-ai"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Get the full Mistral AI configuration
            full_secret_name = self._get_secret_name(secret_name)
            secret = self.secrets_manager.get_secret(full_secret_name)
            await self._cache_secret(secret_name, secret)
            
            # Parse and validate secret structure
            config = secret.as_dict()
            required_fields = ["api_key"]
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Missing required field '{field}' in Mistral AI configuration")
            
            return config
            
        except Exception as e:
            self._handle_secret_error(secret_name, e)
            raise
    
    
    async def get_storage_config(self) -> Dict[str, Any]:
        """
        Get AWS S3 storage configuration.
        
        Returns:
            Dict containing:
            - bucket_name: S3 bucket name
            - region: AWS region
            - access_key_id: AWS access key (if not using IAM roles)
            - secret_access_key: AWS secret key (if not using IAM roles)
            - upload_limits: File size and type limits
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "storage"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Use the convenience method from aws_secrets.py
            config = self.secrets_manager.get_storage_config()
            await self._cache_secret(secret_name, SecretValue(
                value=config,
                version_id="cached",
                created_date="",
                secret_name=secret_name
            ))
            
            required_fields = ["bucket_name", "region"]
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Missing required field '{field}' in storage configuration")
            
            return config
            
        except Exception as e:
            self._handle_secret_error(secret_name, e)
            raise
    
    
    async def get_auth_service_config(self) -> Dict[str, Any]:
        """
        Get external authentication service configuration.
        
        Returns:
            Dict containing:
            - service_url: Auth service base URL
            - api_key: API key for service communication
            - timeout_settings: Request timeout configuration
            - retry_policy: Retry configuration
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "auth-service"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Use the convenience method from aws_secrets.py
            config = self.secrets_manager.get_auth_service_config()
            await self._cache_secret(secret_name, SecretValue(
                value=config,
                version_id="cached",
                created_date="",
                secret_name=secret_name
            ))
            
            required_fields = ["service_url"]
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Missing required field '{field}' in auth service configuration")
            
            return config
            
        except Exception as e:
            self._handle_secret_error(secret_name, e)
            raise


    async def get_database_config(self) -> Dict[str, Any]:
        """
        Get database connection configuration.
        
        Returns:
            Dict containing:
            - connection_string: Database connection string
            - username: Database username
            - password: Database password
            - pool_settings: Connection pool configuration
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "database"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Use the convenience method from aws_secrets.py
            config = self.secrets_manager.get_database_config()
            await self._cache_secret(secret_name, SecretValue(
                value=config,
                version_id="cached",
                created_date="",
                secret_name=secret_name
            ))
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Database configuration not available: {e}")
            return {}


    async def get_jwt_config(self) -> Dict[str, Any]:
        """
        Get JWT configuration for token validation.
        
        Returns:
            Dict containing:
            - public_key: JWT public key for token validation
            - algorithm: JWT algorithm (e.g., RS256, HS256)
            - issuer: Token issuer
            - audience: Token audience
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "jwt"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Use the convenience method from aws_secrets.py
            config = self.secrets_manager.get_jwt_config()
            await self._cache_secret(secret_name, SecretValue(
                value=config,
                version_id="cached",
                created_date="",
                secret_name=secret_name
            ))
            
            required_fields = ["public_key", "algorithm"]
            for field in required_fields:
                if field not in config:
                    raise ConfigurationError(f"Missing required field '{field}' in JWT configuration")
            
            return config
            
        except Exception as e:
            self._handle_secret_error(secret_name, e)
            raise


    async def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Get monitoring and logging configuration.
        
        Returns:
            Dict containing:
            - log_level: Application log level
            - monitoring_endpoints: External monitoring service URLs
            - api_keys: Monitoring service API keys
            - alert_settings: Alert configuration
            
        Raises:
            ConfigurationError: If secrets cannot be retrieved
        """
        secret_name = "monitoring"
        cached_secret = self._get_cached_secret(secret_name)
        if cached_secret:
            return cached_secret.as_dict()
        
        try:
            # Use the convenience method from aws_secrets.py
            config = self.secrets_manager.get_monitoring_config()
            await self._cache_secret(secret_name, SecretValue(
                value=config,
                version_id="cached",
                created_date="",
                secret_name=secret_name
            ))
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Monitoring configuration not available: {e}")
            return {"log_level": "INFO"}


    async def refresh_secrets(self) -> bool:
        """
        Refresh all cached secrets from AWS Secrets Manager.
        
        This method should be called periodically to ensure secrets
        are up-to-date, especially for rotating secrets.
        
        Returns:
            bool: True if all secrets were refreshed successfully
            
        Raises:
            ConfigurationError: If critical secrets cannot be refreshed
        """
        try:
            self.logger.info("Refreshing all cached secrets")
            
            # Clear cache
            self._cache.clear()
            
            # Try to reload critical secrets
            critical_secrets = ["mistral-ai", "storage", "auth-service"]
            success_count = 0
            
            for secret_name in critical_secrets:
                try:
                    if secret_name == "mistral-ai":
                        await self.get_mistral_ai_config()
                    elif secret_name == "storage":
                        await self.get_storage_config()
                    elif secret_name == "auth-service":
                        await self.get_auth_service_config()
                    success_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to refresh secret '{secret_name}': {e}")
            
            self.logger.info(f"Successfully refreshed {success_count}/{len(critical_secrets)} critical secrets")
            return success_count == len(critical_secrets)
            
        except Exception as e:
            self.logger.error(f"Error during secret refresh: {e}")
            return False


    async def validate_secrets(self) -> Dict[str, bool]:
        """
        Validate all required secrets are available and properly formatted.
        
        Returns:
            Dict mapping secret names to validation status
            
        Raises:
            ConfigurationError: If critical secrets are missing or invalid
        """
        validation_results = {}
        
        # Validate critical secrets
        secret_validators = {
            "mistral-ai": self.get_mistral_ai_config,
            "storage": self.get_storage_config,
            "auth-service": self.get_auth_service_config,
            "jwt": self.get_jwt_config,
            "monitoring": self.get_monitoring_config,
        }
        
        for secret_name, validator in secret_validators.items():
            try:
                await validator()
                validation_results[secret_name] = True
                self.logger.debug(f"Secret '{secret_name}' validation passed")
            except Exception as e:
                validation_results[secret_name] = False
                self.logger.error(f"Secret '{secret_name}' validation failed: {e}")
        
        return validation_results


    def _get_secret_name(self, secret_type: str) -> str:
        """
        Generate the full secret name for AWS Secrets Manager.
        
        Args:
            secret_type: Type of secret (e.g., 'mistral-ai', 'storage', 'database')
            
        Returns:
            str: Full secret name with prefix and environment
        """
        # The AWSSecretsManager now handles environment prefixing automatically
        return secret_type


    def _handle_secret_error(self, secret_name: str, error: Exception) -> None:
        """
        Handle errors when retrieving secrets.
        
        Args:
            secret_name: Name of the secret that failed
            error: The exception that occurred
            
        Raises:
            ConfigurationError: Always, with appropriate error message
        """
        error_msg = f"Failed to retrieve secret '{secret_name}': {str(error)}"
        self.logger.error(error_msg)
        raise ConfigurationError(error_msg) from error


    async def _cache_secret(self, secret_name: str, secret_value: SecretValue) -> None:
        """
        Cache a secret value with TTL.
        
        Args:
            secret_name: Name of the secret
            secret_value: Secret value to cache
        """
        import time
        self._cache[secret_name] = {
            "secret": secret_value,
            "timestamp": time.time()
        }
        self.logger.debug(f"Cached secret '{secret_name}'")


    def _get_cached_secret(self, secret_name: str) -> Optional[SecretValue]:
        """
        Retrieve a secret from cache if available and not expired.
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            SecretValue if cached and valid, None otherwise
        """
        if secret_name not in self._cache:
            return None
        
        import time
        cache_entry = self._cache[secret_name]
        
        # Check if cache entry is expired
        if (time.time() - cache_entry["timestamp"]) > self._cache_ttl:
            del self._cache[secret_name]
            return None
        
        return cache_entry["secret"]


# Global secrets manager instance
_secrets_manager: Optional[DocumentServiceSecretsManager] = None


def get_secrets_manager(environment: str = "production", aws_region: str = "ap-east-1") -> DocumentServiceSecretsManager:
    """
    Get the global secrets manager instance.
    
    Args:
        environment: Environment name (development, staging, production)
        aws_region: AWS region for Secrets Manager
        
    Returns:
        DocumentServiceSecretsManager: Global secrets manager instance
    """
    global _secrets_manager
    
    if _secrets_manager is None:
        _secrets_manager = DocumentServiceSecretsManager(environment, aws_region)
    
    return _secrets_manager


async def initialize_secrets(environment: str = "production", aws_region: str = "ap-east-1") -> None:
    """
    Initialize and validate all application secrets.
    
    This function should be called during application startup to:
    - Load all required secrets
    - Validate secret format and content
    - Cache secrets for performance
    - Fail fast if critical secrets are missing
    
    Args:
        environment: Environment name (development, staging, production)
        aws_region: AWS region for Secrets Manager
    
    Raises:
        ConfigurationError: If initialization fails
    """
    secrets_manager = get_secrets_manager(environment, aws_region)
    
    try:
        # Validate all critical secrets
        validation_results = await secrets_manager.validate_secrets()
        
        failed_secrets = [name for name, status in validation_results.items() if not status]
        if failed_secrets:
            raise ConfigurationError(f"Failed to initialize secrets: {failed_secrets}")
        
        logging.getLogger(__name__).info("Successfully initialized all application secrets")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to initialize secrets: {e}")
        raise


async def health_check_secrets() -> Dict[str, Any]:
    """
    Perform health check on secrets management.
    
    Returns:
        Dict containing:
        - status: "healthy" | "degraded" | "unhealthy"
        - secrets_available: Count of available secrets
        - last_refresh: Timestamp of last refresh
        - errors: List of any errors encountered
    """
    if _secrets_manager is None:
        return {
            "status": "unhealthy",
            "secrets_available": 0,
            "last_refresh": None,
            "errors": ["Secrets manager not initialized"]
        }
    
    try:
        # Test AWS connection
        connection_test = _secrets_manager.secrets_manager.test_connection()
        
        # Validate secrets
        validation_results = await _secrets_manager.validate_secrets()
        
        available_count = sum(1 for status in validation_results.values() if status)
        total_count = len(validation_results)
        
        failed_secrets = [name for name, status in validation_results.items() if not status]
        
        # Determine overall status
        if not connection_test:
            status = "unhealthy"
            errors = ["AWS Secrets Manager connection failed"]
        elif failed_secrets:
            status = "degraded"
            errors = [f"Failed secrets: {', '.join(failed_secrets)}"]
        else:
            status = "healthy"
            errors = []
        
        return {
            "status": status,
            "secrets_available": available_count,
            "total_secrets": total_count,
            "aws_connection": connection_test,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "secrets_available": 0,
            "total_secrets": 0,
            "aws_connection": False,
            "errors": [str(e)]
        }
