# Authentication Service Integration

This document describes how the Document Service integrates with the existing Authentication microservice.

## 🏗️ Architecture Overview

The Document Service follows microservice architecture principles by:
- **NOT reimplementing authentication logic** locally
- **Using the existing Auth Service** as an external dependency
- **Acting as a client** to the Auth Service APIs
- **Maintaining service boundaries** and separation of concerns

```
┌─────────────────────┐     HTTP/REST     ┌─────────────────────┐
│                     │ ◄────────────────► │                     │
│  Document Service   │                   │  Auth Service       │
│  (Port: 8001)       │  Token Verify     │  (Port: 8000)       │
│                     │  User Info        │                     │
└─────────────────────┘                   └─────────────────────┘
         │                                           │
         ▼                                           ▼
┌─────────────────────┐                   ┌─────────────────────┐
│  Document Database  │                   │  Auth Database      │
│  (PostgreSQL)       │                   │  (Supabase)         │
└─────────────────────┘                   └─────────────────────┘
```

## 🔗 Integration Points

### 1. **Token Verification**
- Document Service receives JWT tokens from clients
- Calls Auth Service `/api/v1/auth/tokens/verify` endpoint
- Validates token authenticity and expiration

### 2. **User Information**
- Retrieves user details via `/api/v1/auth/sessions/current`
- Caches user info to reduce API calls
- Uses user ID for document ownership

### 3. **Permission Checking**
- Validates user permissions for document operations
- Implements role-based access control (RBAC)
- Calls Auth Service for permission validation

## 📡 API Communication

### **Request Flow Example**

1. **Client Request**:
   ```http
   POST /api/v1/documents/upload
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   Content-Type: multipart/form-data
   ```

2. **Document Service → Auth Service**:
   ```http
   POST http://auth-service:8000/api/v1/auth/tokens/verify
   {
     "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   }
   ```

3. **Auth Service Response**:
   ```json
   {
     "success": true,
     "data": {
       "is_valid": true,
       "user_id": "550e8400-e29b-41d4-a716-446655440000",
       "expires_at": "2024-01-15T11:30:00Z"
     }
   }
   ```

4. **Document Service Processes Request** with authenticated user context

## 🔧 Implementation Details

### **AuthClientService Class**
```python
class AuthClientService:
    """Client for auth microservice communication"""
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token with auth service"""
        
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get user information from auth service"""
        
    async def check_user_permissions(self, user_id: str, permissions: List[str]) -> bool:
        """Check if user has required permissions"""
```

### **Authentication Middleware**
```python
class AuthMiddleware:
    """FastAPI middleware for request authentication"""
    
    async def authenticate_request(self, authorization_header: str) -> Dict[str, Any]:
        """Authenticate incoming requests"""
```

### **FastAPI Dependencies**
```python
async def get_current_user(authorization: str = Header()) -> Dict[str, Any]:
    """FastAPI dependency for authenticated user"""

def require_permissions(permissions: List[str]):
    """FastAPI dependency factory for permission checking"""
```

## ⚙️ Configuration

### **Environment Variables**
```env
# Authentication Service
AUTH_SERVICE_URL=http://auth-service:8000
AUTH_SERVICE_TIMEOUT=30
AUTH_SERVICE_RETRIES=3
AUTH_TOKEN_CACHE_TTL=300
AUTH_USER_CACHE_TTL=600
```

### **Service Discovery**
- Use Kubernetes service discovery in production
- Docker Compose networking for development
- AWS Load Balancer for production deployment

## 🔄 Error Handling

### **Auth Service Unavailable**
```python
try:
    await auth_client.verify_token(token)
except AuthenticationError:
    return JSONResponse(
        status_code=503,
        content={"error": "Authentication service unavailable"}
    )
```

### **Circuit Breaker Pattern**
```python
# TODO: Implement circuit breaker for auth service calls
if circuit_breaker.is_open():
    # Fallback to cached token validation
    # Or return service unavailable
```

## 📈 Performance Optimizations

### **Token Caching**
- Cache valid tokens for 5 minutes
- Reduce auth service API calls
- Use Redis for distributed caching

### **User Info Caching**
- Cache user information for 10 minutes
- Include permissions and roles
- Invalidate on user updates

### **Connection Pooling**
- Maintain HTTP connection pool to auth service
- Configure appropriate timeouts
- Implement retry logic with exponential backoff

## 🔒 Security Considerations

### **Token Handling**
- Never log or expose JWT tokens
- Use secure HTTP client configuration
- Implement token blacklist checking

### **Network Security**
- Use HTTPS for auth service communication
- Implement mutual TLS in production
- Network-level firewall rules

### **Error Information**
- Don't expose internal auth service errors
- Use generic error messages for clients
- Log detailed errors for debugging

## 📊 Monitoring & Observability

### **Health Checks**
```python
async def health_check():
    """Include auth service health in overall health"""
    auth_health = await auth_client.health_check()
    return {
        "auth_service": auth_health,
        "status": "healthy" if auth_health["status"] == "healthy" else "degraded"
    }
```

### **Metrics**
- Track auth service response times
- Monitor authentication success/failure rates
- Alert on auth service unavailability

### **Logging**
```python
logger.info(
    "User authenticated",
    extra={
        "user_id": user_data["user_id"],
        "auth_service_response_time": response_time,
        "correlation_id": correlation_id
    }
)
```

## 🚀 Deployment Considerations

### **Development Environment**
```yaml
# docker-compose.yml
version: '3.8'
services:
  auth-service:
    image: insurecove/auth-service:latest
    ports:
      - "8000:8000"
    
  document-service:
    build: .
    ports:
      - "8001:8000"
    environment:
      - AUTH_SERVICE_URL=http://auth-service:8000
    depends_on:
      - auth-service
```

### **Production Environment**
- Use service mesh (Istio) for service-to-service communication
- Implement proper load balancing
- Set up monitoring and alerting
- Configure auto-scaling based on load

## 🧪 Testing Strategy

### **Unit Tests**
- Mock auth service responses
- Test error handling scenarios
- Validate caching behavior

### **Integration Tests**
- Test against real auth service
- Validate end-to-end authentication flow
- Test service failure scenarios

### **Load Tests**
- Test auth service integration under load
- Validate caching effectiveness
- Measure response time impact

## 📋 Implementation Status

### ✅ Completed
- [x] Created `app/services/auth_client_service.py` - Auth microservice client
- [x] Implemented `AuthClientService` class with token validation methods
- [x] Added FastAPI dependency `get_current_user()` for route authentication
- [x] Updated API routes to reference auth_client_service for authentication
- [x] Configured auth service settings in `app/core/config.py`
- [x] Updated environment configuration (.env.example) with auth service URLs
- [x] Updated documentation (PROJECT_STRUCTURE.md, document-service-design.md)
- [x] Created unit test scaffolding for auth client service
- [x] Updated docker-compose.yml with auth service environment variables

### 🔧 TODO Implementation Tasks
- [ ] Complete `AuthClientService.validate_token()` implementation
- [ ] Implement `AuthClientService.get_user_permissions()` method
- [ ] Implement `AuthClientService.verify_document_access()` method
- [ ] Add token caching mechanism with TTL
- [ ] Add circuit breaker pattern for auth service calls
- [ ] Implement health check monitoring for auth service
- [ ] Complete unit tests for auth client service
- [ ] Add integration tests with mock auth service
- [ ] Update API route implementations to use auth dependencies
- [ ] Add comprehensive error handling and fallback strategies

## 📚 References

- [Auth Service API Documentation](../auth_services_api_doc/API_DOCUMENTATION.md)
- [Microservice Architecture Patterns](https://microservices.io/patterns/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)

---

**Last Updated**: July 8, 2025  
**Document Version**: 1.0.0
