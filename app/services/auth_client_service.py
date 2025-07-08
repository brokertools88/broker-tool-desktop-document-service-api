"""
Authentication Client Service for communicating with the auth microservice.

This service handles communication with the external authentication service
following microservice architecture principles.
"""

from typing import Dict, List, Optional, Any
import logging
import httpx
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class AuthClientService:
    """
    Client service for communicating with the authentication microservice.
    
    This service acts as a client to the existing auth microservice rather than
    implementing authentication logic locally, following microservice principles.
    
    TODO:
    - Implement HTTP client with proper timeout and retries
    - Add circuit breaker pattern for resilience
    - Implement token caching for performance
    - Add request/response logging
    - Implement service discovery integration
    - Add health check monitoring for auth service
    """
    
    def __init__(self):
        self.settings = settings
        self.auth_service_url = self.settings.AUTH_SERVICE_URL
        self.timeout = httpx.Timeout(30.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify token with the authentication service.
        
        Args:
            token: JWT access token to verify
            
        Returns:
            Token verification result with user info
            
        Raises:
            AuthenticationError: If token is invalid or expired
            
        TODO:
        - Implement token caching to reduce API calls
        - Add retry logic for network failures
        - Implement token blacklist checking
        - Add correlation ID for request tracing
        """
        try:
            url = f"{self.auth_service_url}/api/v1/auth/tokens/verify"
            payload = {"token": token}
            
            response = await self.client.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result["data"]["is_valid"]:
                    logger.info(f"Token verified successfully for user: {result['data'].get('user_id')}")
                    return result["data"]
                else:
                    logger.warning("Token verification failed: token is invalid")
                    raise AuthenticationError("Invalid token")
            
            elif response.status_code == 401:
                logger.warning("Token verification failed: unauthorized")
                raise AuthenticationError("Token expired or invalid")
            
            else:
                logger.error(f"Auth service error: {response.status_code} - {response.text}")
                raise AuthenticationError("Authentication service error")
                
        except httpx.TimeoutException:
            logger.error("Auth service timeout during token verification")
            raise AuthenticationError("Authentication service timeout")
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {str(e)}")
            raise AuthenticationError("Authentication service unavailable")
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {str(e)}")
            raise AuthenticationError("Authentication verification failed")
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Get current user information from authentication service.
        
        Args:
            token: JWT access token
            
        Returns:
            User information dictionary
            
        TODO:
        - Implement user info caching
        - Add user permission/role retrieval
        - Implement user profile caching
        """
        try:
            url = f"{self.auth_service_url}/api/v1/auth/sessions/current"
            headers = {"Authorization": f"Bearer {token}"}
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"User info retrieved for: {result['data']['user'].get('user_id')}")
                    return result["data"]["user"]
                else:
                    raise AuthenticationError("Failed to get user info")
            
            elif response.status_code == 401:
                raise AuthenticationError("Token expired or invalid")
            
            elif response.status_code == 403:
                raise AuthenticationError("Token expired")
            
            else:
                logger.error(f"Auth service error: {response.status_code}")
                raise AuthenticationError("Authentication service error")
                
        except httpx.TimeoutException:
            logger.error("Auth service timeout during user info retrieval")
            raise AuthenticationError("Authentication service timeout")
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {str(e)}")
            raise AuthenticationError("Authentication service unavailable")
    
    async def check_user_permissions(self, user_id: str, required_permissions: List[str]) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user_id: User ID to check permissions for
            required_permissions: List of required permissions
            
        Returns:
            True if user has all required permissions
            
        TODO:
        - Implement permission caching
        - Add role-based permission checking
        - Implement hierarchical permissions
        """
        try:
            # TODO: Call auth service to get user permissions
            # For now, implement basic permission checking
            # This would typically call /api/v1/auth/users/{user_id}/permissions
            
            url = f"{self.auth_service_url}/api/v1/auth/users/{user_id}/permissions"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                result = response.json()
                user_permissions = result.get("data", {}).get("permissions", [])
                return all(perm in user_permissions for perm in required_permissions)
            
            return False
            
        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of authentication service.
        
        Returns:
            Health status information
            
        TODO:
        - Implement comprehensive health monitoring
        - Add response time tracking
        - Implement circuit breaker integration
        """
        try:
            url = f"{self.auth_service_url}/health/ready"
            response = await self.client.get(url)
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "status_code": response.status_code,
                "last_checked": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Auth service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close HTTP client connections."""
        await self.client.aclose()


class AuthMiddleware:
    """
    Authentication middleware for FastAPI that uses the auth microservice.
    
    TODO:
    - Implement FastAPI middleware integration
    - Add automatic token extraction from headers
    - Implement user context injection
    - Add permission-based route protection
    """
    
    def __init__(self, auth_client: AuthClientService):
        self.auth_client = auth_client
    
    async def authenticate_request(self, authorization_header: Optional[str]) -> Dict[str, Any]:
        """
        Authenticate request using authorization header.
        
        Args:
            authorization_header: Authorization header value
            
        Returns:
            User information if authenticated
            
        Raises:
            AuthenticationError: If authentication fails
            
        TODO:
        - Implement bearer token extraction
        - Add API key authentication support
        - Implement request context management
        """
        if not authorization_header:
            raise AuthenticationError("Missing authorization header")
        
        if not authorization_header.startswith("Bearer "):
            raise AuthenticationError("Invalid authorization header format")
        
        token = authorization_header[7:]  # Remove "Bearer " prefix
        
        # Verify token with auth service
        token_data = await self.auth_client.verify_token(token)
        
        # Get full user information
        user_data = await self.auth_client.get_current_user(token)
        
        return {
            "user": user_data,
            "token_data": token_data
        }


# TODO: Add dependency injection for FastAPI
def get_auth_client() -> AuthClientService:
    """
    Dependency provider for auth client service.
    
    TODO:
    - Implement proper dependency injection
    - Add connection pooling
    - Implement singleton pattern if needed
    """
    return AuthClientService()


# TODO: Add authentication dependencies for FastAPI routes
async def get_current_user(
    authorization: Optional[str] = None,
    auth_client: Optional[AuthClientService] = None
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user.
    
    TODO:
    - Implement as proper FastAPI dependency
    - Add automatic header extraction
    - Implement user caching
    """
    if not auth_client:
        auth_client = get_auth_client()
    
    middleware = AuthMiddleware(auth_client)
    return await middleware.authenticate_request(authorization)


# TODO: Add permission checking dependencies
def require_permissions(permissions: List[str]):
    """
    FastAPI dependency factory for permission checking.
    
    Args:
        permissions: List of required permissions
        
    Returns:
        FastAPI dependency function
        
    TODO:
    - Implement as FastAPI dependency factory
    - Add role-based checking
    - Implement permission caching
    """
    async def permission_checker(
        current_user: Optional[Dict[str, Any]] = None,
        auth_client: Optional[AuthClientService] = None
    ):
        if not auth_client:
            auth_client = get_auth_client()
        
        if not current_user:
            raise AuthenticationError("User authentication required")
        
        user_id = current_user["user"]["user_id"]
        has_permissions = await auth_client.check_user_permissions(user_id, permissions)
        
        if not has_permissions:
            raise AuthorizationError(f"Missing required permissions: {permissions}")
        
        return current_user
    
    return permission_checker
