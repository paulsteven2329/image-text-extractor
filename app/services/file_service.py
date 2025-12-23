"""File validation and handling service."""

import os
from typing import Tuple, Optional
from fastapi import UploadFile
from PIL import Image
import aiofiles
from loguru import logger

from app.core.config import settings
from app.core.exceptions import FileValidationError, UnsupportedFileTypeError
from app.models import ImageFormat


class FileService:
    """Service for file validation and handling."""
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_EXTENSIONS
        self.upload_dir = settings.UPLOAD_DIR
    
    def validate_file_type(self, filename: str) -> bool:
        """Validate if file type is supported."""
        if not filename:
            return False
        
        file_ext = os.path.splitext(filename)[1].lower()
        return file_ext in self.allowed_extensions
    
    def validate_file_size(self, file_size: int) -> bool:
        """Validate if file size is within limits."""
        return file_size <= self.max_file_size
    
    async def validate_image_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded image file."""
        try:
            # Check file name
            if not file.filename:
                raise FileValidationError("File name is required")
            
            # Check file type
            if not self.validate_file_type(file.filename):
                raise UnsupportedFileTypeError(
                    f"Unsupported file type. Allowed formats: {', '.join(self.allowed_extensions)}"
                )
            
            # Read file content for validation
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Check file size
            if not self.validate_file_size(len(content)):
                raise FileValidationError(
                    f"File size too large. Maximum allowed: {self.max_file_size / (1024*1024):.1f}MB"
                )
            
            # Validate image content using PIL
            try:
                image = Image.open(file.file)
                image.verify()  # Verify image integrity
                await file.seek(0)  # Reset file pointer after verification
                
                # Check image dimensions (optional)
                if image.size[0] < 10 or image.size[1] < 10:
                    raise FileValidationError("Image dimensions too small (minimum 10x10 pixels)")
                
                return True, None
                
            except Exception as e:
                raise FileValidationError(f"Invalid image file: {str(e)}")
                
        except (FileValidationError, UnsupportedFileTypeError):
            raise
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            raise FileValidationError(f"File validation failed: {str(e)}")
    
    async def save_uploaded_file(self, file: UploadFile, filename: str) -> str:
        """Save uploaded file to disk."""
        try:
            file_path = os.path.join(self.upload_dir, filename)
            
            # Ensure upload directory exists
            os.makedirs(self.upload_dir, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise FileValidationError(f"Failed to save file: {str(e)}")
    
    def cleanup_file(self, file_path: str) -> None:
        """Clean up temporary file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"File cleaned up: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
    
    def get_image_format(self, file_path: str) -> ImageFormat:
        """Determine image format from file."""
        try:
            with Image.open(file_path) as img:
                format_map = {
                    'JPEG': ImageFormat.JPEG,
                    'PNG': ImageFormat.PNG,
                    'BMP': ImageFormat.BMP,
                    'TIFF': ImageFormat.TIFF,
                    'WEBP': ImageFormat.WEBP,
                    'GIF': ImageFormat.GIF
                }
                return format_map.get(img.format, ImageFormat.JPEG)
        except Exception:
            return ImageFormat.JPEG