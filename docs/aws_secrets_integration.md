# AWS Secrets Manager Integration for Document Service

This document explains the AWS Secrets Manager integration implemented for the InsureCove Document Service, replacing `.env` file usage with secure cloud-based secret management.

## Overview

The document service now uses AWS Secrets Manager for all sensitive configuration instead of `.env` files. This provides:

- **Security**: Encrypted storage of secrets in AWS
- **Rotation**: Automatic secret rotation capabilities
- **Audit**: Comprehensive access logging
- **Environment Separation**: Different secrets per environment
- **Caching**: Performance optimization through intelligent caching

## Architecture

### File Structure

```
app/
├── utils/
│   └── aws_secrets.py          # Core AWS Secrets Manager client
├── services/
│   └── secrets_service.py      # Document service-specific secrets management
├── core/
│   ├── secrets_config.py       # Secrets-based configuration classes
│   └── exceptions.py          # Configuration error handling
└── main.py                    # Application startup with secrets initialization
```

### Component Responsibilities

1. **`aws_secrets.py`** - Core AWS Secrets Manager client
   - Low-level AWS API interactions
   - Caching and performance optimization
   - Error handling and retry logic
   - Proxy support for corporate networks

2. **`secrets_service.py`** - Document service wrapper
   - Application-specific secret retrieval methods
   - Business logic for secret validation
   - High-level configuration interfaces

3. **`secrets_config.py`** - Configuration management
   - Replaces traditional env-based settings
   - Provides property-based access to configuration
   - Automatic fallback to environment variables for non-sensitive settings

## Secret Organization

### Secret Naming Convention

Secrets are organized with the following naming pattern:
```
insurecove/{environment}/{secret_type}
```

Examples:
- `insurecove/production/mistral-ai`
- `insurecove/production/storage`
- `insurecove/production/auth-service`
- `insurecove/staging/database`

### Secret Types

#### 1. Mistral AI Configuration (`mistral-ai`)
```json
{
  "api_key": "your-mistral-api-key",
  "api_endpoint": "https://api.mistral.ai/v1",
  "model_config": {
    "model": "mistral-ocr-latest",
    "timeout": 300
  },
  "rate_limits": {
    "requests_per_hour": 500
  }
}
```

#### 2. Storage Configuration (`storage`)
```json
{
  "bucket_name": "insurecove-documents-prod",
  "region": "ap-east-1",
  "prefix": "documents/",
  "upload_limits": {
    "max_file_size_mb": 50,
    "allowed_file_types": ["pdf", "jpeg", "jpg", "png", "tiff"]
  }
}
```

#### 3. Auth Service Configuration (`auth-service`)
```json
{
  "service_url": "https://auth.insurecove.com",
  "api_key": "your-auth-service-api-key",
  "timeout_settings": {
    "connect_timeout": 30,
    "read_timeout": 60
  },
  "retry_policy": {
    "max_retries": 3,
    "backoff_factor": 2
  }
}
```

#### 4. JWT Configuration (`jwt`)
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\\n...\\n-----END PUBLIC KEY-----",
  "algorithm": "RS256",
  "issuer": "insurecove-auth",
  "audience": "insurecove-services"
}
```

#### 5. Database Configuration (`database`) - Optional
```json
{
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "username": "db_user",
  "password": "db_password",
  "pool_settings": {
    "pool_size": 20,
    "max_overflow": 30
  }
}
```

#### 6. Monitoring Configuration (`monitoring`) - Optional
```json
{
  "log_level": "INFO",
  "sentry_dsn": "https://your-sentry-dsn",
  "monitoring_endpoints": {
    "metrics": "https://metrics.insurecove.com",
    "alerts": "https://alerts.insurecove.com"
  },
  "api_keys": {
    "datadog": "your-datadog-key"
  }
}
```

## Usage Examples

### Application Startup

```python
# main.py
from app.core.secrets_config import initialize_config
from app.services.secrets_service import initialize_secrets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize secrets and configuration
    await initialize_secrets(environment="production")
    config = await initialize_config(environment="production")
    
    print(f"🚀 Document Service starting with {config.environment} configuration")
    yield
    print("🛑 Document Service shutting down...")
```

### Accessing Configuration

```python
# Using the secrets-based configuration
from app.core.secrets_config import get_config

config = get_config()

# Get Mistral AI API key
api_key = config.mistral_api_key

# Get S3 bucket name
bucket = config.aws_s3_bucket

# Get auth service URL
auth_url = config.auth_service_url
```

### Direct Secret Access

```python
# Using the secrets service directly
from app.services.secrets_service import get_secrets_manager

secrets = get_secrets_manager()

# Get full Mistral AI configuration
mistral_config = await secrets.get_mistral_ai_config()
api_key = mistral_config["api_key"]
model = mistral_config["model_config"]["model"]

# Get storage configuration
storage_config = await secrets.get_storage_config()
bucket = storage_config["bucket_name"]
```

## Environment Variables

Non-sensitive configuration still uses environment variables:

### Required Environment Variables
```bash
ENVIRONMENT=production           # or development, staging
AWS_REGION=ap-east-1            # AWS region for Secrets Manager
```

### Optional Environment Variables
```bash
# Server settings
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Feature flags
ENABLE_OCR_AUTO_PROCESSING=true
ENABLE_THUMBNAIL_GENERATION=true
ENABLE_BATCH_PROCESSING=true

# Rate limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
UPLOAD_RATE_LIMIT_PER_HOUR=1000
OCR_RATE_LIMIT_PER_HOUR=500

# Proxy settings (if needed)
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
```

## Health Checks

The service provides health endpoints that verify AWS Secrets Manager connectivity:

```python
# Health check includes secrets status
GET /health/detailed

Response:
{
  "status": "healthy",
  "services": {
    "secrets_manager": {
      "status": "healthy",
      "secrets_available": 5,
      "aws_connection": true
    }
  }
}
```

## Error Handling

Custom exceptions for configuration errors:

```python
from app.core.exceptions import ConfigurationError, SecretsManagerError

try:
    config = await secrets.get_mistral_ai_config()
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    # Handle gracefully
```

## Security Considerations

1. **IAM Permissions**: Service needs appropriate IAM roles/policies for Secrets Manager
2. **Network**: Use VPC endpoints for Secrets Manager access if in private subnets
3. **Caching**: Secrets are cached for 5 minutes to balance performance and security
4. **Rotation**: Secrets support automatic rotation (cache will refresh)
5. **Audit**: All secret access is logged by AWS CloudTrail

## Deployment

### AWS IAM Policy
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "arn:aws:secretsmanager:ap-east-1:*:secret:insurecove/*"
    }
  ]
}
```

### Docker Environment
```dockerfile
# Dockerfile
ENV ENVIRONMENT=production
ENV AWS_REGION=ap-east-1
# No need to set secret values - they come from AWS
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: document-service
spec:
  template:
    spec:
      serviceAccountName: document-service-sa  # With proper IAM role
      containers:
      - name: document-service
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: AWS_REGION
          value: "ap-east-1"
```

## Migration from .env Files

To migrate from `.env` files:

1. **Create secrets in AWS Secrets Manager** using the naming convention above
2. **Update deployment** to remove `.env` file mounting
3. **Set environment variables** for ENVIRONMENT and AWS_REGION
4. **Deploy** - the service will automatically use AWS Secrets Manager

## Development

For local development:

```bash
# Set environment to development
export ENVIRONMENT=development
export AWS_REGION=ap-east-1

# Ensure AWS credentials are configured
aws configure

# Run the service
uvicorn app.main:app --reload
```

The service will automatically use `insurecove/development/*` secrets for development environment.

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure IAM role or AWS credentials are properly configured
2. **Secret Names**: Verify secrets exist with correct naming pattern
3. **Permissions**: Check IAM policy allows access to required secrets
4. **Network**: Verify connectivity to AWS Secrets Manager
5. **Region**: Ensure AWS_REGION matches where secrets are stored

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('app.utils.aws_secrets').setLevel(logging.DEBUG)
logging.getLogger('app.services.secrets_service').setLevel(logging.DEBUG)
```

### Testing Connectivity

```python
# Test AWS Secrets Manager connection
from app.utils.aws_secrets import test_aws_connection

if test_aws_connection():
    print("✅ AWS Secrets Manager connection successful")
else:
    print("❌ AWS Secrets Manager connection failed")
```

This completes the comprehensive AWS Secrets Manager integration for the InsureCove Document Service.
