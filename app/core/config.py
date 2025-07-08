"""
Configuration Management for InsureCove Document Service

This module handles all application configuration using Pydantic settings
with support for environment variables and AWS Secrets Manager.

Author: InsureCove Team
Date: July 8, 2025
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
import os


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


class Settings(BaseSettings):
    """Application configuration settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ============= APPLICATION SETTINGS =============
    APP_NAME: str = "InsureCove Document Service"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    LOG_LEVEL: LogLevel = LogLevel.INFO
    
    # TODO: Add application description
    # TODO: Add contact information
    
    # ============= SERVER SETTINGS =============
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    RELOAD: bool = True
    
    # TODO: Add SSL configuration
    # TODO: Add server timeout settings
    
    # ============= SECURITY SETTINGS =============
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]
    
    # ============= AUTHENTICATION SERVICE =============
    AUTH_SERVICE_URL: str = "http://localhost:8000"  # Auth microservice URL
    AUTH_SERVICE_TIMEOUT: int = 30
    AUTH_SERVICE_RETRIES: int = 3
    AUTH_TOKEN_CACHE_TTL: int = 300  # 5 minutes
    AUTH_USER_CACHE_TTL: int = 600   # 10 minutes
    
    # TODO: Load from AWS Secrets Manager
    # TODO: Add JWT configuration (if local fallback needed)
    # TODO: Add API key settings
    
    # ============= DATABASE SETTINGS =============
    DATABASE_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    # TODO: Add database migration settings
    # TODO: Add connection retry configuration
    
    # ============= AWS CONFIGURATION =============
    AWS_REGION: str = "ap-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_S3_BUCKET: str = "insurecove-documents"
    AWS_S3_PREFIX: str = "documents/"
    
    # TODO: Add AWS Secrets Manager configuration
    # TODO: Add S3 encryption settings
    # TODO: Add IAM role configuration
    
    # ============= STORAGE CONFIGURATION =============
    STORAGE_TYPE: StorageType = StorageType.LOCAL
    LOCAL_STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "jpeg", "jpg", "png", "tiff", "tif"]
    UPLOAD_TIMEOUT_SECONDS: int = 300
    DOWNLOAD_URL_EXPIRY_HOURS: int = 24
    
    # TODO: Add file compression settings
    # TODO: Add thumbnail generation settings
    # TODO: Add file retention policies
    
    # ============= OCR CONFIGURATION =============
    MISTRAL_API_KEY: Optional[str] = None
    MISTRAL_API_URL: str = "https://api.mistral.ai/v1"
    MISTRAL_MODEL: str = "mistral-ocr-latest"
    OCR_TIMEOUT_SECONDS: int = 300
    OCR_MAX_RETRIES: int = 3
    OCR_BATCH_SIZE: int = 10
    
    # TODO: Add OCR quality settings
    # TODO: Add language configuration
    # TODO: Add custom model settings
    
    # ============= CACHE CONFIGURATION =============
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600
    OCR_CACHE_TTL_SECONDS: int = 86400
    DOCUMENT_CACHE_TTL_SECONDS: int = 1800
    CACHE_MAX_CONNECTIONS: int = 50
    
    # TODO: Add cache partitioning
    # TODO: Add cache warming configuration
    
    # ============= RATE LIMITING =============
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 20
    RATE_LIMIT_STORAGE: str = "memory"  # or "redis"
    UPLOAD_RATE_LIMIT_PER_HOUR: int = 1000
    OCR_RATE_LIMIT_PER_HOUR: int = 500
    
    # TODO: Add user-specific rate limits
    # TODO: Add premium tier rate limits
    
    # ============= MONITORING CONFIGURATION =============
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    HEALTH_CHECK_TIMEOUT: int = 30
    LOG_JSON_FORMAT: bool = False
    SENTRY_DSN: Optional[str] = None
    
    # TODO: Add APM configuration
    # TODO: Add alerting configuration
    
    # ============= TASK QUEUE CONFIGURATION =============
    CELERY_BROKER_URL: str = "redis://localhost:6379"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379"
    TASK_QUEUE_NAME: str = "document_processing"
    OCR_QUEUE_NAME: str = "ocr_processing"
    MAX_CONCURRENT_TASKS: int = 5
    
    # TODO: Add task priority configuration
    # TODO: Add retry policies
    
    # ============= PROXY CONFIGURATION =============
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    NO_PROXY: Optional[str] = None
    
    # TODO: Add proxy authentication
    
    # ============= FEATURE FLAGS =============
    ENABLE_OCR_AUTO_PROCESSING: bool = True
    ENABLE_THUMBNAIL_GENERATION: bool = True
    ENABLE_BATCH_PROCESSING: bool = True
    ENABLE_WEBHOOK_NOTIFICATIONS: bool = False
    ENABLE_DOCUMENT_VERSIONING: bool = False
    
    # TODO: Add A/B testing configuration
    # TODO: Add experimental features
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.ENVIRONMENT == Environment.TESTING
    
    def get_database_url(self) -> str:
        """Get database URL with fallback"""
        # TODO: Implement database URL construction
        # TODO: Add connection pooling parameters
        return self.DATABASE_URL or "sqlite:///./document_service.db"
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        # TODO: Parse Redis URL into components
        # TODO: Add connection pool settings
        return {
            "url": self.REDIS_URL,
            "max_connections": self.CACHE_MAX_CONNECTIONS,
            "decode_responses": True
        }
    
    def get_aws_config(self) -> Dict[str, Any]:
        """Get AWS configuration"""
        # TODO: Add STS token support
        # TODO: Add role assumption
        config = {
            "region_name": self.AWS_REGION
        }
        
        if self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY:
            config.update({
                "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY
            })
        
        if self.AWS_SESSION_TOKEN:
            config["aws_session_token"] = self.AWS_SESSION_TOKEN
        
        return config
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration"""
        # TODO: Add storage-specific settings
        if self.STORAGE_TYPE == StorageType.S3:
            return {
                "type": "s3",
                "bucket": self.AWS_S3_BUCKET,
                "prefix": self.AWS_S3_PREFIX,
                "region": self.AWS_REGION
            }
        else:
            return {
                "type": "local",
                "path": self.LOCAL_STORAGE_PATH
            }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        # TODO: Add environment-specific CORS settings
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": self.CORS_CREDENTIALS,
            "allow_methods": self.CORS_METHODS,
            "allow_headers": self.CORS_HEADERS
        }
    
    def get_ocr_config(self) -> Dict[str, Any]:
        """Get OCR service configuration"""
        # TODO: Add OCR model configuration
        # TODO: Add processing options
        return {
            "api_key": self.MISTRAL_API_KEY,
            "api_url": self.MISTRAL_API_URL,
            "model": self.MISTRAL_MODEL,
            "timeout": self.OCR_TIMEOUT_SECONDS,
            "max_retries": self.OCR_MAX_RETRIES,
            "batch_size": self.OCR_BATCH_SIZE
        }
    
    # TODO: Add validation methods
    # TODO: Add configuration loading from AWS Secrets
    # TODO: Add configuration caching
    # TODO: Add configuration refresh mechanism


# Global settings instance
settings = Settings()


# TODO: Add configuration factory
# TODO: Add environment-specific configurations
# TODO: Add configuration validation
# TODO: Add hot reloading for development
