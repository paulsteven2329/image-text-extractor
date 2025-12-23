"""Custom exceptions and exception handlers."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from loguru import logger
from typing import Any, Dict


class OCRError(Exception):
    """Base exception for OCR operations."""
    pass


class ImageProcessingError(Exception):
    """Exception raised during image processing."""
    pass


class FileValidationError(Exception):
    """Exception raised during file validation."""
    pass


class UnsupportedFileTypeError(Exception):
    """Exception raised for unsupported file types."""
    pass


def create_error_response(status_code: int, message: str, details: Any = None) -> Dict[str, Any]:
    """Create standardized error response."""
    error_response = {
        "error": {
            "code": status_code,
            "message": message,
            "timestamp": None
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return error_response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.status_code, exc.detail)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation exceptions."""
    logger.error(f"Validation Exception: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation Error",
            exc.errors()
        )
    )


async def ocr_exception_handler(request: Request, exc: OCRError) -> JSONResponse:
    """Handle OCR exceptions."""
    logger.error(f"OCR Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "OCR Processing Error",
            str(exc)
        )
    )


async def image_processing_exception_handler(request: Request, exc: ImageProcessingError) -> JSONResponse:
    """Handle image processing exceptions."""
    logger.error(f"Image Processing Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Image Processing Error",
            str(exc)
        )
    )


async def file_validation_exception_handler(request: Request, exc: FileValidationError) -> JSONResponse:
    """Handle file validation exceptions."""
    logger.error(f"File Validation Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=create_error_response(
            status.HTTP_400_BAD_REQUEST,
            "File Validation Error",
            str(exc)
        )
    )


async def unsupported_file_exception_handler(request: Request, exc: UnsupportedFileTypeError) -> JSONResponse:
    """Handle unsupported file type exceptions."""
    logger.error(f"Unsupported File Type Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        content=create_error_response(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported File Type",
            str(exc)
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.exception(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error"
        )
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(OCRError, ocr_exception_handler)
    app.add_exception_handler(ImageProcessingError, image_processing_exception_handler)
    app.add_exception_handler(FileValidationError, file_validation_exception_handler)
    app.add_exception_handler(UnsupportedFileTypeError, unsupported_file_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)