"""Health check and system status endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any
from datetime import datetime
import psutil
import os
from loguru import logger

from app.core.config import settings
from app.services import OCRService
from app.models import OCREngine
from app.utils import create_success_response, create_error_response

router = APIRouter()

def get_ocr_service() -> OCRService:
    return OCRService()


@router.get(
    "/",
    summary="Basic health check",
    description="Simple health check endpoint to verify API is running."
)
async def health_check() -> JSONResponse:
    """Basic health check endpoint."""
    return create_success_response(
        data={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.VERSION,
            "service": settings.PROJECT_NAME
        },
        message="Service is healthy"
    )


@router.get(
    "/detailed",
    summary="Detailed health check",
    description="Comprehensive health check including system resources and dependencies."
)
async def detailed_health_check(
    ocr_service: OCRService = Depends(get_ocr_service)
) -> JSONResponse:
    """Detailed health check with system information."""
    
    try:
        # Get system information
        system_info = _get_system_info()
        
        # Check OCR engines availability
        ocr_status = await _check_ocr_engines(ocr_service)
        
        # Check storage
        storage_info = _get_storage_info()
        
        # Overall health status
        overall_status = "healthy"
        issues = []
        
        # Check for issues
        if system_info["memory_usage_percent"] > 90:
            issues.append("High memory usage")
            overall_status = "degraded"
        
        if system_info["disk_usage_percent"] > 95:
            issues.append("Low disk space")
            overall_status = "degraded"
        
        if not ocr_status["tesseract_available"] and not ocr_status["easyocr_available"]:
            issues.append("No OCR engines available")
            overall_status = "unhealthy"
        
        health_data = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": settings.VERSION,
            "service": settings.PROJECT_NAME,
            "system": system_info,
            "ocr_engines": ocr_status,
            "storage": storage_info,
            "issues": issues
        }
        
        status_code = 200 if overall_status == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "success": overall_status == "healthy",
                "message": f"Service is {overall_status}",
                "data": health_data,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
    except Exception as e:
        logger.exception(f"Error during detailed health check: {str(e)}")
        return create_error_response(
            message="Health check failed",
            status_code=503
        )


@router.get(
    "/readiness",
    summary="Readiness probe",
    description="Check if the service is ready to handle requests."
)
async def readiness_check(
    ocr_service: OCRService = Depends(get_ocr_service)
) -> JSONResponse:
    """Readiness probe for Kubernetes/container orchestration."""
    
    try:
        # Check if at least one OCR engine is available
        ocr_status = await _check_ocr_engines(ocr_service)
        
        if not ocr_status["tesseract_available"] and not ocr_status["easyocr_available"]:
            return create_error_response(
                message="No OCR engines available",
                status_code=503
            )
        
        # Check if upload directory is accessible
        if not os.path.exists(settings.UPLOAD_DIR):
            try:
                os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            except Exception:
                return create_error_response(
                    message="Upload directory not accessible",
                    status_code=503
                )
        
        return create_success_response(
            data={
                "ready": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ocr_engines": ocr_status
            },
            message="Service is ready"
        )
        
    except Exception as e:
        logger.exception(f"Error during readiness check: {str(e)}")
        return create_error_response(
            message="Readiness check failed",
            status_code=503
        )


@router.get(
    "/liveness",
    summary="Liveness probe",
    description="Check if the service is alive and should not be restarted."
)
async def liveness_check() -> JSONResponse:
    """Liveness probe for Kubernetes/container orchestration."""
    
    return create_success_response(
        data={
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": _get_uptime()
        },
        message="Service is alive"
    )


def _get_system_info() -> Dict[str, Any]:
    """Get system resource information."""
    try:
        # Memory information
        memory = psutil.virtual_memory()
        
        # Disk information
        disk = psutil.disk_usage('/')
        
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_usage_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 1),
            "cpu_usage_percent": cpu_percent,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": "Unable to get system information"}


async def _check_ocr_engines(ocr_service: OCRService) -> Dict[str, bool]:
    """Check availability of OCR engines."""
    status = {
        "tesseract_available": False,
        "easyocr_available": False
    }
    
    # Test Tesseract
    try:
        import pytesseract
        pytesseract.get_languages()
        status["tesseract_available"] = True
    except Exception as e:
        logger.warning(f"Tesseract not available: {str(e)}")
    
    # Test EasyOCR (basic import test)
    try:
        import easyocr
        status["easyocr_available"] = True
    except Exception as e:
        logger.warning(f"EasyOCR not available: {str(e)}")
        status["easyocr_available"] = False
    
    return status


def _get_storage_info() -> Dict[str, Any]:
    """Get storage information for upload directory."""
    try:
        upload_dir = settings.UPLOAD_DIR
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
        
        # Get directory size
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(upload_dir):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except OSError:
                    pass
        
        return {
            "upload_directory": upload_dir,
            "directory_exists": True,
            "total_size_mb": round(total_size / (1024**2), 2),
            "file_count": file_count
        }
        
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        return {
            "upload_directory": settings.UPLOAD_DIR,
            "directory_exists": False,
            "error": str(e)
        }


def _get_uptime() -> float:
    """Get service uptime in seconds."""
    try:
        return psutil.boot_time()
    except Exception:
        return 0.0