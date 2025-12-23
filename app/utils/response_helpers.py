"""Response helper utilities."""

from typing import Dict, Any, Optional
from fastapi import status
from fastapi.responses import JSONResponse
from datetime import datetime


def create_success_response(
    data: Any,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response."""
    
    response_data = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    
    response_data = {
        "success": False,
        "error": {
            "code": status_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    if details:
        response_data["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_validation_error_response(
    errors: list,
    message: str = "Validation failed"
) -> JSONResponse:
    """Create a validation error response."""
    
    return create_error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": errors}
    )


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_processing_time(seconds: float) -> str:
    """Format processing time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"