"""
InsureCove Document Service - Metrics Routes

Production metrics collection:
- GET /metrics (detailed JSON metrics)
- GET /metrics/summary (summary metrics)
- GET /metrics/prometheus (Prometheus format)
- GET /metrics/documents (document-specific metrics)
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Response, Request
from fastapi.responses import PlainTextResponse
import psutil

from app.models import MetricsResponse

# Initialize router
router = APIRouter()

# Simple in-memory metrics store (in production, use Redis or similar)
metrics_store = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "requests_by_status": {},
    "response_times": [],
    "errors_total": 0,
    "document_events": {
        "uploads_total": 0,
        "downloads_total": 0,
        "deletions_total": 0,
        "processing_failures": 0,
        "total_storage_used_mb": 0.0
    },
    "ocr_events": {
        "jobs_total": 0,
        "jobs_successful": 0,
        "jobs_failed": 0,
        "total_processing_time": 0.0
    },
    "start_time": time.time()
}


def update_request_metrics(endpoint: str, status_code: int, response_time: float):
    """Update request metrics"""
    metrics_store["requests_total"] += 1
    
    # Track by endpoint
    if endpoint not in metrics_store["requests_by_endpoint"]:
        metrics_store["requests_by_endpoint"][endpoint] = 0
    metrics_store["requests_by_endpoint"][endpoint] += 1
    
    # Track by status code
    status_group = f"{status_code // 100}xx"
    if status_group not in metrics_store["requests_by_status"]:
        metrics_store["requests_by_status"][status_group] = 0
    metrics_store["requests_by_status"][status_group] += 1
    
    # Track response times (keep last 1000)
    metrics_store["response_times"].append(response_time)
    if len(metrics_store["response_times"]) > 1000:
        metrics_store["response_times"] = metrics_store["response_times"][-1000:]
    
    # Track errors
    if status_code >= 400:
        metrics_store["errors_total"] += 1


def update_document_metrics(event_type: str, **kwargs):
    """Update document-related metrics"""
    if event_type == "upload":
        metrics_store["document_events"]["uploads_total"] += 1
        if "file_size_mb" in kwargs:
            metrics_store["document_events"]["total_storage_used_mb"] += kwargs["file_size_mb"]
    elif event_type == "download":
        metrics_store["document_events"]["downloads_total"] += 1
    elif event_type == "deletion":
        metrics_store["document_events"]["deletions_total"] += 1
        if "file_size_mb" in kwargs:
            metrics_store["document_events"]["total_storage_used_mb"] -= kwargs["file_size_mb"]
    elif event_type == "processing_failure":
        metrics_store["document_events"]["processing_failures"] += 1


def update_ocr_metrics(event_type: str, **kwargs):
    """Update OCR-related metrics"""
    if event_type == "job_started":
        metrics_store["ocr_events"]["jobs_total"] += 1
    elif event_type == "job_completed":
        metrics_store["ocr_events"]["jobs_successful"] += 1
        if "processing_time" in kwargs:
            metrics_store["ocr_events"]["total_processing_time"] += kwargs["processing_time"]
    elif event_type == "job_failed":
        metrics_store["ocr_events"]["jobs_failed"] += 1


def get_system_metrics() -> Dict[str, Any]:
    """Get system resource metrics"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory_usage_mb": round(memory.used / (1024 * 1024), 2),
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu_percent,
            "uptime_seconds": time.time() - metrics_store["start_time"]
        }
    except Exception:
        return {
            "memory_usage_mb": 0.0,
            "memory_usage_percent": 0.0,
            "cpu_usage_percent": 0.0,
            "uptime_seconds": time.time() - metrics_store["start_time"]
        }


def calculate_metrics() -> Dict[str, Any]:
    """Calculate comprehensive metrics"""
    uptime_seconds = time.time() - metrics_store["start_time"]
    
    # Request metrics
    requests_per_minute = (metrics_store["requests_total"] / (uptime_seconds / 60)) if uptime_seconds > 0 else 0
    
    # Average response time
    avg_response_time = (
        sum(metrics_store["response_times"]) / len(metrics_store["response_times"])
        if metrics_store["response_times"] else 0
    )
    
    # Error rate
    error_rate_percent = (
        (metrics_store["errors_total"] / metrics_store["requests_total"]) * 100
        if metrics_store["requests_total"] > 0 else 0
    )
    
    # OCR success rate
    total_ocr_jobs = metrics_store["ocr_events"]["jobs_total"]
    ocr_success_rate = (
        (metrics_store["ocr_events"]["jobs_successful"] / total_ocr_jobs) * 100
        if total_ocr_jobs > 0 else 100.0
    )
    
    # Average OCR processing time
    avg_ocr_time = (
        metrics_store["ocr_events"]["total_processing_time"] / metrics_store["ocr_events"]["jobs_successful"]
        if metrics_store["ocr_events"]["jobs_successful"] > 0 else 0
    )
    
    # Documents processed today (simplified - in production, track by date)
    documents_today = metrics_store["document_events"]["uploads_total"]
    
    return {
        "total_requests": metrics_store["requests_total"],
        "requests_per_minute": round(requests_per_minute, 2),
        "average_response_time_ms": round(avg_response_time, 2),
        "error_rate_percent": round(error_rate_percent, 2),
        "total_documents": metrics_store["document_events"]["uploads_total"],
        "documents_processed_today": documents_today,
        "total_storage_used_mb": round(metrics_store["document_events"]["total_storage_used_mb"], 2),
        "total_ocr_jobs": total_ocr_jobs,
        "ocr_success_rate_percent": round(ocr_success_rate, 2),
        "average_ocr_time_seconds": round(avg_ocr_time, 2),
        **get_system_metrics()
    }


@router.get(
    "",
    response_model=MetricsResponse,
    summary="Get service metrics",
    description="Comprehensive service metrics in JSON format"
)
async def get_metrics(request: Request) -> MetricsResponse:
    """Get comprehensive service metrics"""
    
    try:
        metrics_data = calculate_metrics()
        
        return MetricsResponse(
            total_requests=metrics_data["total_requests"],
            requests_per_minute=metrics_data["requests_per_minute"],
            average_response_time_ms=metrics_data["average_response_time_ms"],
            error_rate_percent=metrics_data["error_rate_percent"],
            total_documents=metrics_data["total_documents"],
            documents_processed_today=metrics_data["documents_processed_today"],
            total_storage_used_mb=metrics_data["total_storage_used_mb"],
            total_ocr_jobs=metrics_data["total_ocr_jobs"],
            ocr_success_rate_percent=metrics_data["ocr_success_rate_percent"],
            average_ocr_time_seconds=metrics_data["average_ocr_time_seconds"],
            timestamp=datetime.now()
        )
        
    except Exception as e:
        # Return empty metrics in case of error
        return MetricsResponse(
            total_requests=0,
            requests_per_minute=0.0,
            average_response_time_ms=0.0,
            error_rate_percent=0.0,
            total_documents=0,
            documents_processed_today=0,
            total_storage_used_mb=0.0,
            total_ocr_jobs=0,
            ocr_success_rate_percent=0.0,
            average_ocr_time_seconds=0.0,
            timestamp=datetime.now()
        )


@router.get(
    "/summary",
    summary="Get metrics summary",
    description="Summary view of key metrics"
)
async def get_metrics_summary():
    """Get a summary view of key metrics"""
    
    metrics_data = calculate_metrics()
    
    return {
        "service": "document-service",
        "timestamp": datetime.now(),
        "uptime_seconds": metrics_data["uptime_seconds"],
        "health": "healthy",
        "requests": {
            "total": metrics_data["total_requests"],
            "per_minute": metrics_data["requests_per_minute"],
            "error_rate_percent": metrics_data["error_rate_percent"]
        },
        "documents": {
            "total_uploaded": metrics_data["total_documents"],
            "processed_today": metrics_data["documents_processed_today"],
            "storage_used_mb": metrics_data["total_storage_used_mb"]
        },
        "ocr": {
            "total_jobs": metrics_data["total_ocr_jobs"],
            "success_rate_percent": metrics_data["ocr_success_rate_percent"],
            "average_time_seconds": metrics_data["average_ocr_time_seconds"]
        },
        "system": {
            "memory_usage_mb": metrics_data["memory_usage_mb"],
            "cpu_usage_percent": metrics_data["cpu_usage_percent"]
        }
    }


@router.get(
    "/prometheus",
    response_class=PlainTextResponse,
    summary="Get Prometheus metrics",
    description="Metrics in Prometheus format for monitoring systems"
)
async def get_prometheus_metrics():
    """Get metrics in Prometheus format"""
    
    metrics_data = calculate_metrics()
    
    prometheus_output = f"""# HELP document_service_requests_total Total number of requests
# TYPE document_service_requests_total counter
document_service_requests_total {metrics_data["total_requests"]}

# HELP document_service_requests_per_minute Current requests per minute
# TYPE document_service_requests_per_minute gauge
document_service_requests_per_minute {metrics_data["requests_per_minute"]}

# HELP document_service_response_time_ms Average response time in milliseconds
# TYPE document_service_response_time_ms gauge
document_service_response_time_ms {metrics_data["average_response_time_ms"]}

# HELP document_service_error_rate_percent Error rate percentage
# TYPE document_service_error_rate_percent gauge
document_service_error_rate_percent {metrics_data["error_rate_percent"]}

# HELP document_service_documents_total Total documents uploaded
# TYPE document_service_documents_total counter
document_service_documents_total {metrics_data["total_documents"]}

# HELP document_service_storage_used_mb Total storage used in MB
# TYPE document_service_storage_used_mb gauge
document_service_storage_used_mb {metrics_data["total_storage_used_mb"]}

# HELP document_service_ocr_jobs_total Total OCR jobs processed
# TYPE document_service_ocr_jobs_total counter
document_service_ocr_jobs_total {metrics_data["total_ocr_jobs"]}

# HELP document_service_ocr_success_rate_percent OCR success rate percentage
# TYPE document_service_ocr_success_rate_percent gauge
document_service_ocr_success_rate_percent {metrics_data["ocr_success_rate_percent"]}

# HELP document_service_memory_usage_mb Memory usage in MB
# TYPE document_service_memory_usage_mb gauge
document_service_memory_usage_mb {metrics_data["memory_usage_mb"]}

# HELP document_service_cpu_usage_percent CPU usage percentage
# TYPE document_service_cpu_usage_percent gauge
document_service_cpu_usage_percent {metrics_data["cpu_usage_percent"]}

# HELP document_service_uptime_seconds Service uptime in seconds
# TYPE document_service_uptime_seconds gauge
document_service_uptime_seconds {metrics_data["uptime_seconds"]}
"""
    
    return prometheus_output


@router.get(
    "/documents",
    summary="Get document-specific metrics",
    description="Detailed metrics about document processing"
)
async def get_document_metrics():
    """Get detailed document processing metrics"""
    
    return {
        "documents": {
            "uploads_total": metrics_store["document_events"]["uploads_total"],
            "downloads_total": metrics_store["document_events"]["downloads_total"],
            "deletions_total": metrics_store["document_events"]["deletions_total"],
            "processing_failures": metrics_store["document_events"]["processing_failures"],
            "total_storage_used_mb": round(metrics_store["document_events"]["total_storage_used_mb"], 2)
        },
        "ocr": {
            "jobs_total": metrics_store["ocr_events"]["jobs_total"],
            "jobs_successful": metrics_store["ocr_events"]["jobs_successful"],
            "jobs_failed": metrics_store["ocr_events"]["jobs_failed"],
            "total_processing_time_seconds": round(metrics_store["ocr_events"]["total_processing_time"], 2),
            "success_rate_percent": round(
                (metrics_store["ocr_events"]["jobs_successful"] / metrics_store["ocr_events"]["jobs_total"]) * 100
                if metrics_store["ocr_events"]["jobs_total"] > 0 else 100.0, 2
            )
        },
        "requests_by_endpoint": metrics_store["requests_by_endpoint"],
        "requests_by_status": metrics_store["requests_by_status"],
        "timestamp": datetime.now()
    }


# Helper functions for other modules to update metrics
def record_request(endpoint: str, status_code: int, response_time: float):
    """Record a request for metrics tracking"""
    update_request_metrics(endpoint, status_code, response_time)


def record_document_event(event_type: str, **kwargs):
    """Record a document event for metrics tracking"""
    update_document_metrics(event_type, **kwargs)


def record_ocr_event(event_type: str, **kwargs):
    """Record an OCR event for metrics tracking"""
    update_ocr_metrics(event_type, **kwargs)
