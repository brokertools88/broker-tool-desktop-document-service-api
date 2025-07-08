"""
InsureCove Document Service - Health Check Routes

Health monitoring endpoints for comprehensive service health monitoring:
- GET /health (overall health status)
- GET /health/live (liveness probe for Kubernetes)
- GET /health/ready (readiness probe for Kubernetes)
- GET /health/startup (startup probe for Kubernetes)
- GET /health/detailed (detailed service health with metrics)

This module provides health checks for:
- AWS S3 storage connectivity
- Mistral AI OCR service
- External authentication service
- System resource usage
- Service dependencies
"""

import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, status
import psutil

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.models import HealthCheckResponse, HealthStatus, ServiceHealthCheck

# Initialize router with tags (prefix will be added in main.py)
router = APIRouter(tags=["health"])

# Initialize logger
logger = get_logger(__name__)

# Application start time for uptime calculation
app_start_time = time.time()

# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings"""
    global settings
    if settings is None:
        settings = Settings()
    return settings


async def check_storage_health() -> ServiceHealthCheck:
    """
    Check AWS S3 storage connectivity and accessibility.
    
    Returns:
        ServiceHealthCheck: Health status of the storage service
    """
    try:
        start_time = time.time()
        
        # TODO: Implement actual S3 health check when storage service is complete
        # This should test:
        # - S3 bucket accessibility
        # - Upload/download permissions
        # - Network connectivity to AWS
        
        # For now, simulate a health check
        await asyncio.sleep(0.01)  # Simulate S3 API call time
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthCheck(
            name="aws_s3_storage",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            error_message=None,
            last_check=datetime.now()
        )
    except Exception as e:
        logger.error(f"Storage health check failed: {str(e)}")
        return ServiceHealthCheck(
            name="aws_s3_storage",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=None,
            error_message=f"S3 storage error: {str(e)}",
            last_check=datetime.now()
        )


async def check_ocr_service_health() -> ServiceHealthCheck:
    """
    Check Mistral AI OCR service connectivity and functionality.
    
    Returns:
        ServiceHealthCheck: Health status of the OCR service
    """
    try:
        start_time = time.time()
        
        # TODO: Implement actual Mistral AI OCR health check when OCR service is complete
        # This should test:
        # - Mistral AI API endpoint availability
        # - API key validation
        # - OCR processing capabilities
        # - Rate limits and quotas
        
        # For now, simulate a health check
        await asyncio.sleep(0.012)  # Simulate Mistral AI API call time
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthCheck(
            name="mistral_ai_ocr",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            error_message=None,
            last_check=datetime.now()
        )
    except Exception as e:
        logger.error(f"OCR service health check failed: {str(e)}")
        return ServiceHealthCheck(
            name="mistral_ai_ocr", 
            status=HealthStatus.UNHEALTHY,
            response_time_ms=None,
            error_message=f"Mistral AI OCR service error: {str(e)}",
            last_check=datetime.now()
        )


async def check_auth_service_health() -> ServiceHealthCheck:
    """
    Check external authentication service connectivity.
    
    Returns:
        ServiceHealthCheck: Health status of the auth service
    """
    try:
        start_time = time.time()
        
        # TODO: Implement actual auth service health check when auth client is complete
        # This should test:
        # - Auth service endpoint availability
        # - Token validation endpoint
        # - Network connectivity
        
        # For now, simulate a health check
        await asyncio.sleep(0.008)  # Simulate auth service API call time
        
        response_time = (time.time() - start_time) * 1000
        
        return ServiceHealthCheck(
            name="external_auth_service",
            status=HealthStatus.HEALTHY,
            response_time_ms=response_time,
            error_message=None,
            last_check=datetime.now()
        )
    except Exception as e:
        logger.error(f"Auth service health check failed: {str(e)}")
        return ServiceHealthCheck(
            name="external_auth_service",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=None,
            error_message=f"Auth service error: {str(e)}",
            last_check=datetime.now()
        )


def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system resource metrics.
    
    Returns:
        Dict[str, Any]: System metrics including CPU, memory, and disk usage
    """
    try:
        # CPU usage (1-second interval for accuracy)
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_mb = memory.used / (1024 * 1024)
        
        # Disk usage (for root partition)
        try:
            disk = psutil.disk_usage('/')
        except:
            # Windows fallback
            disk = psutil.disk_usage('C:\\')
        disk_used_percent = (disk.used / disk.total) * 100
        
        # Process-specific metrics
        process = psutil.Process()
        process_memory_mb = process.memory_info().rss / (1024 * 1024)
        
        return {
            "cpu_usage_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(memory_used_mb, 2),
            "memory_usage_percent": round(memory.percent, 2),
            "disk_usage_percent": round(disk_used_percent, 2),
            "process_memory_mb": round(process_memory_mb, 2),
            "uptime_seconds": round(time.time() - app_start_time, 2)
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        return {
            "cpu_usage_percent": 0.0,
            "memory_usage_mb": 0.0,
            "memory_usage_percent": 0.0,
            "disk_usage_percent": 0.0,
            "process_memory_mb": 0.0,
            "uptime_seconds": round(time.time() - app_start_time, 2)
        }


def determine_overall_status(dependencies: List[ServiceHealthCheck]) -> HealthStatus:
    """
    Determine overall service status based on dependency health.
    
    Args:
        dependencies: List of service health checks
        
    Returns:
        HealthStatus: Overall service status
    """
    if not dependencies:
        return HealthStatus.DEGRADED
    
    unhealthy_count = sum(1 for dep in dependencies if dep.status == HealthStatus.UNHEALTHY)
    degraded_count = sum(1 for dep in dependencies if dep.status == HealthStatus.DEGRADED)
    
    # If any critical service is unhealthy, mark as unhealthy
    critical_services = ["aws_s3_storage", "external_auth_service"]
    for dep in dependencies:
        if dep.name in critical_services and dep.status == HealthStatus.UNHEALTHY:
            return HealthStatus.UNHEALTHY
    
    # If more than half of services are unhealthy, mark as unhealthy
    if unhealthy_count > len(dependencies) / 2:
        return HealthStatus.UNHEALTHY
    
    # If any service is degraded or unhealthy, mark as degraded
    if degraded_count > 0 or unhealthy_count > 0:
        return HealthStatus.DEGRADED
    
    return HealthStatus.HEALTHY


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Overall health check",
    description="Get comprehensive health status of the document service"
)
async def health_check(request: Request) -> HealthCheckResponse:
    """
    Get overall application health status with dependency checks.
    
    This endpoint performs comprehensive health checks on all service dependencies
    and returns detailed status information.
    
    Returns:
        HealthCheckResponse: Comprehensive health information
    """
    try:
        logger.info("Performing comprehensive health check")
        
        # Check all service dependencies
        dependencies = []
        
        # Storage health check
        storage_check = await check_storage_health()
        dependencies.append(storage_check)
        
        # OCR service health check
        ocr_check = await check_ocr_service_health()
        dependencies.append(ocr_check)
        
        # Auth service health check
        auth_check = await check_auth_service_health()
        dependencies.append(auth_check)
        
        # Determine overall status
        overall_status = determine_overall_status(dependencies)
        
        # Get system metrics
        system_metrics = get_system_metrics()
        
        # Build response
        response = HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=getattr(get_settings(), 'app_version', '1.0.0'),
            uptime_seconds=system_metrics["uptime_seconds"],
            dependencies=dependencies,
            storage_health={
                "s3_accessible": storage_check.status == HealthStatus.HEALTHY,
                "response_time_ms": storage_check.response_time_ms,
                "last_check": storage_check.last_check.isoformat()
            },
            ocr_service_health={
                "mistral_ai_accessible": ocr_check.status == HealthStatus.HEALTHY,
                "response_time_ms": ocr_check.response_time_ms,
                "last_check": ocr_check.last_check.isoformat()
            },
            cache_health={
                "status": "not_configured",
                "details": "No caching service configured for this service"
            },
            memory_usage_mb=system_metrics["memory_usage_mb"],
            cpu_usage_percent=system_metrics["cpu_usage_percent"],
            disk_usage_percent=system_metrics["disk_usage_percent"]
        )
        
        logger.info(f"Health check completed - Status: {overall_status}")
        return response
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.now(),
            version=getattr(get_settings(), 'app_version', '1.0.0'),
            uptime_seconds=time.time() - app_start_time,
            dependencies=[],
            storage_health={"status": "unknown", "error": str(e)},
            ocr_service_health={"status": "unknown", "error": str(e)},
            cache_health={"status": "unknown", "error": str(e)},
            memory_usage_mb=None,
            cpu_usage_percent=None,
            disk_usage_percent=None
        )


@router.get(
    "/live",
    summary="Liveness probe",
    description="Kubernetes liveness probe - checks if service is running"
)
async def liveness_probe():
    """
    Simple liveness check for Kubernetes.
    
    This endpoint should return 200 as long as the service process is running.
    It performs minimal checks to avoid affecting service performance.
    
    Returns:
        dict: Simple status response
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(),
        "uptime_seconds": round(time.time() - app_start_time, 2)
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Kubernetes readiness probe - checks if service is ready to serve traffic"
)
async def readiness_probe():
    """
    Readiness check for Kubernetes load balancing.
    
    This endpoint checks if the service is ready to serve traffic by verifying
    that critical dependencies are available.
    
    Returns:
        dict: Readiness status
        
    Raises:
        HTTPException: 503 if service is not ready
    """
    try:
        logger.debug("Performing readiness check")
        
        # Quick check of critical services only
        storage_check = await check_storage_health()
        auth_check = await check_auth_service_health()
        
        # Service is not ready if critical dependencies are unhealthy
        if storage_check.status == HealthStatus.UNHEALTHY or auth_check.status == HealthStatus.UNHEALTHY:
            logger.warning("Service not ready - critical dependencies unhealthy")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready - critical dependencies unavailable"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.now(),
            "storage": storage_check.status.value,
            "auth": auth_check.status.value,
            "uptime_seconds": round(time.time() - app_start_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get(
    "/startup",
    summary="Startup probe",
    description="Kubernetes startup probe - checks if service has finished starting"
)
async def startup_probe():
    """
    Startup check for Kubernetes.
    
    This endpoint checks if the service has finished its startup sequence.
    It should only return 200 when the service is fully initialized.
    
    Returns:
        dict: Startup status
        
    Raises:
        HTTPException: 503 if service is still starting up
    """
    # Service is considered started after 30 seconds of uptime
    # This gives time for all initialization to complete
    uptime = time.time() - app_start_time
    startup_threshold = 30.0
    
    if uptime < startup_threshold:
        logger.info(f"Service still starting up - uptime: {uptime:.1f}s < {startup_threshold}s")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service still starting up - {uptime:.1f}s elapsed"
        )
    
    return {
        "status": "started",
        "timestamp": datetime.now(),
        "uptime_seconds": round(uptime, 2),
        "startup_completed": True
    }


@router.get(
    "/detailed",
    response_model=HealthCheckResponse,
    summary="Detailed health check",
    description="Comprehensive health status with detailed metrics and logging"
)
async def detailed_health_check(request: Request) -> HealthCheckResponse:
    """
    Get detailed health information with comprehensive logging.
    
    This endpoint is the same as the main health check but with additional
    logging and detailed metrics collection for troubleshooting.
    
    Returns:
        HealthCheckResponse: Detailed health information
    """
    logger.info("Performing detailed health check with comprehensive logging")
    
    # Get the standard health check response
    result = await health_check(request)
    
    # Log detailed results for debugging
    logger.info(f"Detailed health check completed - Overall Status: {result.status}")
    logger.info(f"Service version: {result.version}")
    logger.info(f"Uptime: {result.uptime_seconds:.2f} seconds")
    
    # Log each dependency status
    for dep in result.dependencies:
        logger.info(
            f"Dependency '{dep.name}': {dep.status} "
            f"(Response time: {dep.response_time_ms}ms)"
        )
        if dep.error_message:
            logger.warning(f"Dependency '{dep.name}' error: {dep.error_message}")
    
    # Log system metrics
    logger.info(f"System metrics - CPU: {result.cpu_usage_percent}%, "
               f"Memory: {result.memory_usage_mb}MB, "
               f"Disk: {result.disk_usage_percent}%")
    
    return result
