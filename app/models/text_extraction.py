"""Pydantic models for text extraction."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class OCREngine(str, Enum):
    """Supported OCR engines."""
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


class ImageFormat(str, Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"
    WEBP = "webp"
    GIF = "gif"


class TextExtractionRequest(BaseModel):
    """Request model for text extraction."""
    ocr_engine: Optional[OCREngine] = OCREngine.TESSERACT
    languages: Optional[List[str]] = Field(default=["en"], description="Languages for OCR")
    preprocess: Optional[bool] = Field(default=True, description="Apply image preprocessing")
    confidence_threshold: Optional[float] = Field(default=0.5, ge=0.0, le=1.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "ocr_engine": "tesseract",
                "languages": ["en"],
                "preprocess": True,
                "confidence_threshold": 0.5
            }
        }


class BoundingBox(BaseModel):
    """Bounding box coordinates for detected text."""
    x: int = Field(description="X coordinate of top-left corner")
    y: int = Field(description="Y coordinate of top-left corner")
    width: int = Field(description="Width of bounding box")
    height: int = Field(description="Height of bounding box")


class TextRegion(BaseModel):
    """Text region with bounding box and confidence."""
    text: str = Field(description="Extracted text")
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0)
    bounding_box: BoundingBox = Field(description="Bounding box coordinates")


class TextExtractionResult(BaseModel):
    """Result model for text extraction."""
    success: bool = Field(description="Whether extraction was successful")
    extracted_text: str = Field(description="Full extracted text")
    text_regions: List[TextRegion] = Field(description="Individual text regions with details")
    confidence_score: float = Field(description="Overall confidence score")
    language_detected: Optional[str] = Field(description="Detected language")
    processing_time: float = Field(description="Processing time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "extracted_text": "Hello World",
                "text_regions": [
                    {
                        "text": "Hello World",
                        "confidence": 0.95,
                        "bounding_box": {
                            "x": 10,
                            "y": 20,
                            "width": 100,
                            "height": 30
                        }
                    }
                ],
                "confidence_score": 0.95,
                "language_detected": "en",
                "processing_time": 1.25
            }
        }


class TextExtractionResponse(BaseModel):
    """Response model for text extraction API."""
    request_id: str = Field(description="Unique request identifier")
    result: TextExtractionResult = Field(description="Extraction result")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    timestamp: datetime = Field(description="Response timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
                "result": {
                    "success": True,
                    "extracted_text": "Hello World",
                    "text_regions": [],
                    "confidence_score": 0.95,
                    "language_detected": "en",
                    "processing_time": 1.25
                },
                "metadata": {
                    "image_size": "1024x768",
                    "image_format": "png",
                    "ocr_engine": "tesseract"
                },
                "timestamp": "2023-12-23T10:30:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: Dict[str, Any] = Field(description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": 400,
                    "message": "Invalid file format",
                    "details": "Supported formats: jpg, jpeg, png, bmp, tiff, webp, gif"
                }
            }
        }