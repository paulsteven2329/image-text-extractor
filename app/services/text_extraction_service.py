"""Main text extraction service orchestrating all components."""

import uuid
import os
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile
from loguru import logger

from app.services.file_service import FileService
from app.services.image_processing_service import ImageProcessingService
from app.services.ocr_service import OCRService
from app.models import (
    OCREngine, 
    TextExtractionRequest, 
    TextExtractionResult,
    TextExtractionResponse
)
from app.core.exceptions import OCRError, ImageProcessingError


class TextExtractionService:
    """Main service for orchestrating text extraction from images."""
    
    def __init__(self):
        self.file_service = FileService()
        self.image_processing_service = ImageProcessingService()
        self.ocr_service = OCRService()
    
    async def extract_text_from_image(
        self,
        file: UploadFile,
        request_params: TextExtractionRequest
    ) -> TextExtractionResponse:
        """Main method to extract text from uploaded image."""
        
        request_id = str(uuid.uuid4())
        temp_files = []  # Track temporary files for cleanup
        
        try:
            logger.info(f"Starting text extraction for request {request_id}")
            
            # Step 1: Validate uploaded file
            await self.file_service.validate_image_file(file)
            
            # Step 2: Save uploaded file
            filename = f"{request_id}_{file.filename}"
            image_path = await self.file_service.save_uploaded_file(file, filename)
            temp_files.append(image_path)
            
            # Step 3: Get image metadata
            image_format = self.file_service.get_image_format(image_path)
            image_info = self.image_processing_service.get_image_info(image_path)
            
            # Step 4: Preprocess image if requested
            processed_image_path = image_path
            if request_params.preprocess:
                try:
                    processed_image_path = self.image_processing_service.preprocess_image(
                        image_path, enhance=True
                    )
                    temp_files.append(processed_image_path)
                except ImageProcessingError as e:
                    logger.warning(f"Image preprocessing failed, using original: {str(e)}")
                    # Continue with original image if preprocessing fails
            
            # Step 5: Extract text using OCR
            ocr_result = self.ocr_service.extract_text(
                processed_image_path,
                engine=request_params.ocr_engine,
                languages=request_params.languages,
                confidence_threshold=request_params.confidence_threshold
            )
            
            # Step 6: Create result object
            extraction_result = TextExtractionResult(
                success=ocr_result['success'],
                extracted_text=ocr_result['extracted_text'],
                text_regions=ocr_result['text_regions'],
                confidence_score=ocr_result['confidence_score'],
                language_detected=ocr_result['language_detected'],
                processing_time=ocr_result['processing_time']
            )
            
            # Step 7: Prepare metadata
            metadata = {
                'image_size': f"{image_info.get('width', 0)}x{image_info.get('height', 0)}",
                'image_format': image_format.value,
                'ocr_engine': request_params.ocr_engine.value,
                'preprocessed': request_params.preprocess,
                'languages': request_params.languages,
                'confidence_threshold': request_params.confidence_threshold,
                'original_filename': file.filename
            }
            
            # Step 8: Create response
            response = TextExtractionResponse(
                request_id=request_id,
                result=extraction_result,
                metadata=metadata,
                timestamp=datetime.utcnow()
            )
            
            logger.info(
                f"Text extraction completed for request {request_id}. "
                f"Extracted {len(extraction_result.extracted_text)} characters "
                f"with confidence {extraction_result.confidence_score:.2f}"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Text extraction failed for request {request_id}: {str(e)}")
            raise
        
        finally:
            # Cleanup temporary files
            self._cleanup_temp_files(temp_files)
    
    def _cleanup_temp_files(self, file_paths: list) -> None:
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                self.file_service.cleanup_file(file_path)
            except Exception as e:
                logger.error(f"Error during cleanup of {file_path}: {str(e)}")
    
    async def get_extraction_capabilities(self) -> Dict[str, Any]:
        """Get information about available extraction capabilities."""
        return {
            'supported_engines': [engine.value for engine in OCREngine],
            'supported_formats': [
                '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'
            ],
            'tesseract_languages': self.ocr_service.get_supported_languages(OCREngine.TESSERACT),
            'easyocr_languages': self.ocr_service.get_supported_languages(OCREngine.EASYOCR),
            'max_file_size_mb': self.file_service.max_file_size / (1024 * 1024),
            'preprocessing_available': True,
            'features': {
                'text_regions': True,
                'confidence_scores': True,
                'bounding_boxes': True,
                'language_detection': True,
                'image_preprocessing': True
            }
        }