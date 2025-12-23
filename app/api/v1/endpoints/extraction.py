"""Simplified text extraction API endpoints."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from typing import Optional
import uuid
import os
import tempfile
import time
from datetime import datetime
from loguru import logger

router = APIRouter()


@router.post(
    "/extract",
    summary="Extract text from image",
    description="Upload an image file and extract text using OCR"
)
async def extract_text(
    file: UploadFile = File(..., description="Image file to extract text from"),
    ocr_engine: str = Form(default="tesseract", description="OCR engine to use"),
    languages: str = Form(default="en", description="Language codes"),
    confidence_threshold: float = Form(default=0.3, description="Confidence threshold")
):
    """Extract text from uploaded image file."""
    
    request_id = str(uuid.uuid4())
    temp_file_path = None
    start_time = time.time()
    
    try:
        logger.info(f"Starting text extraction for request {request_id}")
        
        # Validate file
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid file with filename required"
            )
        
        # Check file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file_ext}"
            )
        
        # Validate parameters
        if ocr_engine not in ["tesseract", "easyocr"]:
            ocr_engine = "tesseract"  # Default fallback
        
        if not (0.0 <= confidence_threshold <= 1.0):
            confidence_threshold = 0.3  # Default fallback
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file_path = temp_file.name
            contents = await file.read()
            temp_file.write(contents)
        
        logger.debug(f"Saved uploaded file to {temp_file_path}")
        
        # Process with OCR service
        from app.services.ocr_service import OCRService
        from app.models import OCREngine
        
        ocr_service = OCRService()
        
        # Parse languages
        language_list = [lang.strip() for lang in languages.split(',') if lang.strip()]
        if not language_list:
            language_list = ['en']
        
        # Extract text
        result = ocr_service.extract_text(
            image_path=temp_file_path,
            engine=OCREngine(ocr_engine),
            languages=language_list,
            confidence_threshold=confidence_threshold
        )
        
        # Get image info
        from PIL import Image
        with Image.open(temp_file_path) as img:
            width, height = img.size
            format_name = img.format.lower() if img.format else 'unknown'
        
        processing_time = time.time() - start_time
        
        # Create response
        response = {
            "request_id": request_id,
            "result": {
                "success": result.get("success", True),
                "extracted_text": result.get("extracted_text", ""),
                "text_regions": [
                    {
                        "text": region.text,
                        "confidence": region.confidence,
                        "bounding_box": {
                            "x": region.bounding_box.x,
                            "y": region.bounding_box.y,
                            "width": region.bounding_box.width,
                            "height": region.bounding_box.height
                        }
                    } for region in result.get("text_regions", [])
                ],
                "confidence_score": result.get("confidence_score", 0.0),
                "language_detected": result.get("language_detected", "unknown"),
                "processing_time": processing_time
            },
            "metadata": {
                "image_size": f"{width}x{height}",
                "image_format": format_name,
                "ocr_engine": ocr_engine,
                "preprocessed": True,
                "languages": language_list,
                "confidence_threshold": confidence_threshold,
                "original_filename": file.filename
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Text extraction completed for request {request_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in text extraction for request {request_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text extraction failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {e}")


@router.get(
    "/supported-engines",
    summary="Get supported OCR engines",
    description="Get list of available OCR engines"
)
async def get_supported_engines():
    """Get list of supported OCR engines."""
    return {
        "engines": [
            {
                "name": "tesseract",
                "description": "Google's Tesseract OCR engine",
                "available": True
            },
            {
                "name": "easyocr", 
                "description": "EasyOCR engine with deep learning",
                "available": False
            }
        ]
    }