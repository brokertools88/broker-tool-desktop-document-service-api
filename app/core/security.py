"""
Security Utilities and Middleware for InsureCove Document Service

This module provides security utilities, middleware, and helper functions
for authentication, authorization, and security hardening.

Author: InsureCove Team
Date: July 8, 2025
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any, Callable
import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta
import re
import mimetypes
import uuid
from pathlib import Path

# TODO: Import configuration
# from app.core.config import settings
# from app.core.exceptions import AuthenticationError, ValidationError


class SecurityConfig:
    """Security configuration constants"""
    
    # File security
    MAX_FILENAME_LENGTH = 255
    BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.scr', '.vbs', '.js', '.jar'}
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/tiff',
        'image/tif'
    }
    
    # Content security
    MALICIOUS_PATTERNS = [
        b'<script',
        b'javascript:',
        b'eval(',
        b'<iframe',
        b'<object',
        b'<embed',
        b'vbscript:',
        b'data:text/html'
    ]
    
    # Password security
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]'
    )
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = "100/minute"
    UPLOAD_RATE_LIMIT = "10/minute"
    OCR_RATE_LIMIT = "50/hour"


class JWTHandler:
    """JWT token handling utilities"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.security = HTTPBearer()
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        # TODO: Load expiry from configuration
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=30)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        """Extract current user from JWT token"""
        payload = self.decode_token(credentials.credentials)
        
        # TODO: Add user validation
        # TODO: Check token blacklist
        # TODO: Validate user permissions
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return payload


class FileSecurityValidator:
    """File upload security validation"""
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename or len(filename) > SecurityConfig.MAX_FILENAME_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename length"
            )
        
        # TODO: Sanitize filename
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Check for blocked extensions
        file_ext = Path(filename).suffix.lower()
        if file_ext in SecurityConfig.BLOCKED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{file_ext}' not allowed"
            )
        
        return sanitized
    
    @staticmethod
    def validate_mime_type(content_type: str, filename: str) -> bool:
        """Validate file MIME type"""
        if content_type not in SecurityConfig.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MIME type '{content_type}' not allowed"
            )
        
        # TODO: Verify MIME type matches file extension
        # TODO: Perform deep content inspection
        
        return True
    
    @staticmethod
    async def scan_file_content(content: bytes) -> bool:
        """Scan file content for malicious patterns"""
        content_lower = content.lower()
        
        for pattern in SecurityConfig.MALICIOUS_PATTERNS:
            if pattern in content_lower:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Malicious content detected in file"
                )
        
        # TODO: Add advanced malware scanning
        # TODO: Integrate with antivirus API
        # TODO: Check file headers for consistency
        
        return True
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {max_size_mb}MB limit"
            )
        
        return True


class APIKeyValidator:
    """API key validation utilities"""
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_api_key(api_key: str, salt: str) -> str:
        """Hash API key with salt"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            api_key.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
    
    @staticmethod
    def verify_api_key(api_key: str, hashed_key: str, salt: str) -> bool:
        """Verify API key against hash"""
        return hmac.compare_digest(
            hashed_key,
            APIKeyValidator.hash_api_key(api_key, salt)
        )


class RequestValidator:
    """Request validation utilities"""
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_input(input_string: str, max_length: int = 1000) -> str:
        """Sanitize user input"""
        if not input_string:
            return ""
        
        # Truncate if too long
        sanitized = input_string[:max_length]
        
        # TODO: Add HTML/script tag removal
        # TODO: Add SQL injection prevention
        # TODO: Add XSS prevention
        
        return sanitized.strip()


class SecurityHeaders:
    """Security headers middleware utilities"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


class RateLimiter:
    """Rate limiting utilities"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        # TODO: Initialize rate limiting backend
        # TODO: Add memory-based fallback
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """Check if request exceeds rate limit"""
        # TODO: Implement sliding window rate limiting
        # TODO: Add burst allowance
        # TODO: Return rate limit headers
        
        return True  # Placeholder
    
    async def increment_counter(self, key: str, window_seconds: int = 60) -> int:
        """Increment rate limit counter"""
        # TODO: Implement counter increment
        # TODO: Set expiry for automatic cleanup
        
        return 1  # Placeholder
    
    def get_rate_limit_key(self, request: Request, identifier: Optional[str] = None) -> str:
        """Generate rate limit key"""
        if identifier:
            return f"rate_limit:{identifier}"
        
        # Use IP address as fallback
        client_ip = self.get_client_ip(request)
        return f"rate_limit:ip:{client_ip}"
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP address"""
        # Check for X-Forwarded-For header (load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"


class PermissionChecker:
    """Permission and authorization utilities"""
    
    @staticmethod
    def check_document_access(user_id: str, document_owner_id: str) -> bool:
        """Check if user can access document"""
        # TODO: Implement role-based access control
        # TODO: Add shared document permissions
        # TODO: Add organization-level permissions
        
        return user_id == document_owner_id
    
    @staticmethod
    def check_admin_permission(user_roles: List[str]) -> bool:
        """Check if user has admin permissions"""
        admin_roles = {"admin", "super_admin", "system_admin"}
        return any(role in admin_roles for role in user_roles)
    
    @staticmethod
    def check_ocr_permission(user_id: str, subscription_level: str = "free") -> bool:
        """Check if user can perform OCR operations"""
        # TODO: Implement subscription-based limits
        # TODO: Check usage quotas
        # TODO: Add rate limiting per user
        
        return True  # Placeholder


# ============= DEPENDENCY INJECTION =============

def get_jwt_handler() -> JWTHandler:
    """Get JWT handler dependency"""
    # TODO: Load secret from configuration/AWS Secrets
    secret_key = "your-secret-key"  # Placeholder
    return JWTHandler(secret_key)


def get_current_user(jwt_handler: JWTHandler = Depends(get_jwt_handler)):
    """Get current user dependency"""
    return jwt_handler.get_current_user


def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get admin user dependency"""
    user_roles = current_user.get("roles", [])
    if not PermissionChecker.check_admin_permission(user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    return current_user


def require_document_access(document_owner_id: str):
    """Require document access permission"""
    def dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_id = current_user.get("sub")
        if not user_id or not PermissionChecker.check_document_access(user_id, document_owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this document"
            )
        return current_user
    return dependency


# ============= UTILITY FUNCTIONS =============

def generate_secure_filename(original_filename: str) -> str:
    """Generate secure filename with timestamp"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(4)
    
    # Sanitize original filename
    safe_name = FileSecurityValidator.validate_filename(original_filename)
    name, ext = Path(safe_name).stem, Path(safe_name).suffix
    
    return f"{timestamp}_{random_suffix}_{name}{ext}"


def create_file_hash(content: bytes) -> str:
    """Create SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()


def verify_file_integrity(content: bytes, expected_hash: str) -> bool:
    """Verify file integrity using hash"""
    actual_hash = create_file_hash(content)
    return hmac.compare_digest(actual_hash, expected_hash)


# TODO: Add encryption utilities
# TODO: Add digital signature verification
# TODO: Add certificate validation
# TODO: Add audit logging
# TODO: Add security monitoring
# TODO: Add threat detection
