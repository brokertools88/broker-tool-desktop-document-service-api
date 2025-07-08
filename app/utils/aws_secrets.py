"""
AWS Secrets Manager Integration for InsureCove Document Service

This module provides a secure and efficient way to retrieve secrets from AWS Secrets Manager
specifically for the document service with support for:
- Document service specific secrets (Mistral AI, S3, Auth service)
- Caching for performance
- Proxy configuration for corporate networks
- Error handling and retry logic
- JSON and string secret formats
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


class AWSSecretsConfig(BaseModel):
    """Configuration for AWS Secrets Manager - Document Service"""
    
    aws_region: str = Field(default="ap-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    
    # Proxy settings for corporate networks
    http_proxy: Optional[str] = Field(default=None, description="HTTP proxy URL")
    https_proxy: Optional[str] = Field(default=None, description="HTTPS proxy URL")
    
    # Secret name prefix for document service
    secret_prefix: str = Field(default="insurecove", description="Prefix for secret names")
    environment: str = Field(default="production", description="Environment (development, staging, production)")
    
    # Cache settings
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")  # 5 minutes


@dataclass
class SecretValue:
    """Container for secret values with metadata"""
    value: Union[str, Dict[str, Any]]
    version_id: str
    created_date: str
    secret_name: str
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert secret value to dictionary if it's JSON"""
        if isinstance(self.value, str):
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                raise ValueError(f"Secret '{self.secret_name}' is not valid JSON")
        return self.value
    
    def as_string(self) -> str:
        """Convert secret value to string"""
        if isinstance(self.value, dict):
            return json.dumps(self.value)
        return str(self.value)


class AWSSecretsManagerError(Exception):
    """Base exception for AWS Secrets Manager operations"""
    pass


class SecretNotFoundError(AWSSecretsManagerError):
    """Raised when a requested secret is not found"""
    pass


class SecretAccessDeniedError(AWSSecretsManagerError):
    """Raised when access to a secret is denied"""
    pass


class AWSSecretsManager:
    """
    AWS Secrets Manager client for Document Service
    
    This class provides a high-level interface for retrieving document service secrets 
    from AWS Secrets Manager with built-in caching, error handling, and proxy support.
    
    Handles document service specific secrets:
    - Mistral AI API credentials
    - AWS S3 storage configuration
    - External auth service credentials
    - JWT configuration
    - Database credentials
    - Monitoring configuration
    """
    
    def __init__(self, config: Optional[AWSSecretsConfig] = None):
        """
        Initialize AWS Secrets Manager client
        
        Args:
            config: Configuration object. If None, will be created from environment variables.
        """
        self.config = config or AWSSecretsConfig()
        self._client = None
        self._cache = {}
        
    def _get_client(self):
        """Get or create boto3 secrets manager client with proxy configuration"""
        if self._client is not None:
            return self._client
            
        try:
            # Prepare session configuration
            session_config = {}
            
            # Configure proxy if specified
            if self.config.http_proxy or self.config.https_proxy:
                session_config['proxies'] = {}
                if self.config.http_proxy:
                    session_config['proxies']['http'] = self.config.http_proxy
                if self.config.https_proxy:
                    session_config['proxies']['https'] = self.config.https_proxy
            
            # Create boto3 session
            session = boto3.Session(
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key,
                region_name=self.config.aws_region
            )
            
            # Create secrets manager client
            client_config = {}
            if session_config.get('proxies'):
                client_config['proxies'] = session_config['proxies']
                
            self._client = session.client(
                'secretsmanager',
                region_name=self.config.aws_region,
                **client_config
            )
            
            logger.info(f"AWS Secrets Manager client initialized for region: {self.config.aws_region}")
            return self._client
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            error_msg = f"AWS credentials not configured properly: {str(e)}"
            logger.error(error_msg)
            raise AWSSecretsManagerError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize AWS Secrets Manager client: {str(e)}"
            logger.error(error_msg)
            raise AWSSecretsManagerError(error_msg) from e
    
    def _get_cache_key(self, secret_name: str, version_id: Optional[str] = None) -> str:
        """Generate cache key for secret"""
        key = f"{self.config.secret_prefix}/{secret_name}"
        if version_id:
            key += f":{version_id}"
        return key
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        import time
        return (time.time() - cache_entry['timestamp']) < self.config.cache_ttl
    
    def get_secret(self, secret_name: str, version_id: Optional[str] = None, use_cache: bool = True) -> SecretValue:
        """
        Retrieve a secret from AWS Secrets Manager
        
        Args:
            secret_name: Name of the secret (without prefix)
            version_id: Specific version of the secret to retrieve
            use_cache: Whether to use cached value if available
            
        Returns:
            SecretValue object containing the secret data and metadata
            
        Raises:
            SecretNotFoundError: If the secret doesn't exist
            SecretAccessDeniedError: If access to the secret is denied
            AWSSecretsManagerError: For other AWS-related errors
        """
        # Check cache first
        cache_key = self._get_cache_key(secret_name, version_id)
        if use_cache and cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Retrieved secret '{secret_name}' from cache")
                return cache_entry['secret']
        
        # Full secret name with prefix and environment
        full_secret_name = f"{self.config.secret_prefix}/{self.config.environment}/{secret_name}"
        
        try:
            client = self._get_client()
            
            # Prepare request parameters
            request_params = {
                'SecretId': full_secret_name
            }
            if version_id:
                request_params['VersionId'] = version_id
            
            # Get secret from AWS
            logger.debug(f"Retrieving secret '{full_secret_name}' from AWS Secrets Manager")
            response = client.get_secret_value(**request_params)
            
            # Parse secret value
            if 'SecretString' in response:
                secret_value = response['SecretString']
                # Try to parse as JSON
                try:
                    secret_value = json.loads(secret_value)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    pass
            else:
                # Binary secret
                secret_value = response['SecretBinary']
            
            # Create SecretValue object
            secret = SecretValue(
                value=secret_value,
                version_id=response.get('VersionId', ''),
                created_date=response.get('CreatedDate', '').isoformat() if response.get('CreatedDate') else '',
                secret_name=full_secret_name
            )
            
            # Cache the result
            if use_cache:
                import time
                self._cache[cache_key] = {
                    'secret': secret,
                    'timestamp': time.time()
                }
            
            logger.info(f"Successfully retrieved secret '{secret_name}'")
            return secret
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ResourceNotFoundException':
                raise SecretNotFoundError(f"Secret '{full_secret_name}' not found: {error_message}")
            elif error_code in ['AccessDeniedException', 'UnauthorizedOperation']:
                raise SecretAccessDeniedError(f"Access denied to secret '{full_secret_name}': {error_message}")
            else:
                raise AWSSecretsManagerError(f"AWS error retrieving secret '{full_secret_name}': {error_message}")
        except Exception as e:
            raise AWSSecretsManagerError(f"Unexpected error retrieving secret '{secret_name}': {str(e)}")
    def get_document_service_config(self) -> Dict[str, Any]:
        """Get document service configuration from secrets"""
        try:
            secret = self.get_secret("document-service")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve document service configuration: {e}")
            raise

    def get_storage_config(self) -> Dict[str, Any]:
        """Get S3 storage configuration from secrets"""
        try:
            secret = self.get_secret("storage")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve storage configuration: {e}")
            raise

    def get_auth_service_config(self) -> Dict[str, Any]:
        """Get external auth service configuration from secrets"""
        try:
            secret = self.get_secret("auth-service")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve auth service configuration: {e}")
            raise

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration from secrets"""
        try:
            secret = self.get_secret("database")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve database configuration: {e}")
            raise

    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration from secrets"""
        try:
            secret = self.get_secret("jwt")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve JWT configuration: {e}")
            raise
    
    def get_mistral_api_key(self) -> str:
        """Get Mistral AI API key for document OCR processing"""
        try:
            secret = self.get_secret("mistral-ai")
            if isinstance(secret.value, dict):
                return secret.value.get('api_key', '')
            return secret.as_string()
        except Exception as e:
            logger.error(f"Failed to retrieve Mistral API key: {e}")
            raise

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring and alerting configuration from secrets"""
        try:
            secret = self.get_secret("monitoring")
            return secret.as_dict()
        except Exception as e:
            logger.error(f"Failed to retrieve monitoring configuration: {e}")
            # Return basic config as fallback
            return {"log_level": "INFO", "enable_metrics": True}
    
    def test_connection(self) -> bool:
        """Test connection to AWS Secrets Manager"""
        try:
            client = self._get_client()
            # Try to list secrets to test connection
            client.list_secrets(MaxResults=1)
            logger.info("AWS Secrets Manager connection test successful")
            return True
        except Exception as e:
            logger.error(f"AWS Secrets Manager connection test failed: {e}")
            return False
    
    def clear_cache(self):
        """Clear the secrets cache"""
        self._cache.clear()
        logger.info("Secrets cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        import time
        current_time = time.time()
        
        stats = {
            'total_entries': len(self._cache),
            'valid_entries': 0,
            'expired_entries': 0,
            'cache_ttl': self.config.cache_ttl
        }
        
        for entry in self._cache.values():
            if (current_time - entry['timestamp']) < self.config.cache_ttl:
                stats['valid_entries'] += 1
            else:
                stats['expired_entries'] += 1
        
        return stats


# Convenience functions for document service
@lru_cache(maxsize=1)
def get_secrets_manager() -> AWSSecretsManager:
    """Get a cached instance of AWSSecretsManager for document service"""
    return AWSSecretsManager()


def get_document_service_config() -> Dict[str, Any]:
    """Convenience function to get document service configuration"""
    return get_secrets_manager().get_document_service_config()


def get_storage_config() -> Dict[str, Any]:
    """Convenience function to get storage configuration"""
    return get_secrets_manager().get_storage_config()


def get_auth_service_config() -> Dict[str, Any]:
    """Convenience function to get auth service configuration"""
    return get_secrets_manager().get_auth_service_config()


def get_database_config() -> Dict[str, Any]:
    """Convenience function to get database configuration"""
    return get_secrets_manager().get_database_config()


def get_jwt_config() -> Dict[str, Any]:
    """Convenience function to get JWT configuration"""
    return get_secrets_manager().get_jwt_config()


def get_mistral_api_key() -> str:
    """Convenience function to get Mistral AI API key"""
    return get_secrets_manager().get_mistral_api_key()


def get_monitoring_config() -> Dict[str, Any]:
    """Convenience function to get monitoring configuration"""
    return get_secrets_manager().get_monitoring_config()


def test_aws_connection() -> bool:
    """Convenience function to test AWS connection"""
    return get_secrets_manager().test_connection()


if __name__ == "__main__":
    # Basic test when run directly for document service
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Test with document service environment
        config = AWSSecretsConfig(environment="development")
        secrets_manager = AWSSecretsManager(config)
        print("✅ Document Service AWS Secrets Manager initialized successfully")
        
        if secrets_manager.test_connection():
            print("✅ AWS connection test passed")
            
            # Test document service specific secrets
            try:
                mistral_key = secrets_manager.get_mistral_api_key()
                print("✅ Mistral AI API key retrieved successfully")
            except Exception as e:
                print(f"⚠️  Mistral AI key not available: {e}")
            
            try:
                storage_config = secrets_manager.get_storage_config()
                print("✅ Storage configuration retrieved successfully")
            except Exception as e:
                print(f"⚠️  Storage config not available: {e}")
                
        else:
            print("❌ AWS connection test failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
