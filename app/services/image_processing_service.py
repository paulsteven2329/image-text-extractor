"""Image preprocessing service for OCR optimization."""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional
from loguru import logger

from app.core.exceptions import ImageProcessingError


class ImageProcessingService:
    """Service for image preprocessing to improve OCR accuracy."""
    
    def __init__(self):
        self.dpi = 300  # Target DPI for OCR
    
    def preprocess_image(self, image_path: str, enhance: bool = True) -> str:
        """Apply preprocessing pipeline to image."""
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ImageProcessingError(f"Could not read image: {image_path}")
            
            # Apply preprocessing pipeline
            processed_image = self._apply_preprocessing_pipeline(image, enhance)
            
            # Save processed image
            processed_path = image_path.replace('.', '_processed.')
            cv2.imwrite(processed_path, processed_image)
            
            logger.info(f"Image preprocessed: {processed_path}")
            return processed_path
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {str(e)}")
            raise ImageProcessingError(f"Image preprocessing failed: {str(e)}")
    
    def _apply_preprocessing_pipeline(self, image: np.ndarray, enhance: bool) -> np.ndarray:
        """Apply the complete preprocessing pipeline."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        if enhance:
            # Apply enhancement techniques
            enhanced = self._enhance_image(denoised)
            
            # Apply morphological operations
            morphed = self._apply_morphological_operations(enhanced)
            
            # Apply sharpening
            sharpened = self._apply_sharpening(morphed)
            
            # Improve text line separation for better OCR
            final_image = self._improve_line_separation(sharpened)
            
            return final_image
        
        return denoised
    
    def _enhance_image(self, image: np.ndarray) -> np.ndarray:
        """Apply image enhancement techniques."""
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        # Apply bilateral filter for noise reduction while preserving edges
        filtered = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        return filtered
    
    def _apply_morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Apply morphological operations to clean up the image."""
        # Create kernel for morphological operations
        kernel = np.ones((1, 1), np.uint8)
        
        # Apply opening to remove noise
        opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Apply closing to fill gaps
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return closing
    
    def _apply_sharpening(self, image: np.ndarray) -> np.ndarray:
        """Apply sharpening filter to enhance text clarity."""
        # Create sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1, 9, -1],
                          [-1, -1, -1]])
        
        # Apply sharpening
        sharpened = cv2.filter2D(image, -1, kernel)
        
        return sharpened
    
    def _improve_line_separation(self, image: np.ndarray) -> np.ndarray:
        """Improve line separation for better text recognition."""
        try:
            # Apply horizontal morphological operations to separate lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_CLOSE, horizontal_kernel, iterations=1)
            
            # Subtract horizontal lines to improve text separation
            result = cv2.subtract(image, horizontal_lines)
            
            # Apply small vertical kernel to preserve character integrity
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
            result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, vertical_kernel, iterations=1)
            
            return result
        except Exception as e:
            logger.warning(f"Line separation improvement failed: {str(e)}")
            return image
    
    def resize_image_for_ocr(self, image_path: str, scale_factor: float = 2.0) -> str:
        """Resize image to improve OCR accuracy."""
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ImageProcessingError(f"Could not read image: {image_path}")
            
            # Calculate new dimensions
            height, width = image.shape
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Resize using high-quality interpolation
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Save resized image
            resized_path = image_path.replace('.', '_resized.')
            cv2.imwrite(resized_path, resized)
            
            return resized_path
            
        except Exception as e:
            logger.error(f"Image resizing error: {str(e)}")
            raise ImageProcessingError(f"Image resizing failed: {str(e)}")
    
    def convert_to_binary(self, image_path: str) -> str:
        """Convert image to binary (black and white) for better OCR."""
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ImageProcessingError(f"Could not read image: {image_path}")
            
            # Apply Otsu's thresholding
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Save binary image
            binary_path = image_path.replace('.', '_binary.')
            cv2.imwrite(binary_path, binary)
            
            return binary_path
            
        except Exception as e:
            logger.error(f"Binary conversion error: {str(e)}")
            raise ImageProcessingError(f"Binary conversion failed: {str(e)}")
    
    def get_image_info(self, image_path: str) -> dict:
        """Get image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height
                }
        except Exception as e:
            logger.error(f"Error getting image info: {str(e)}")
            return {}