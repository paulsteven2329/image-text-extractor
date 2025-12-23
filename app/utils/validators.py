"""Validation utility functions."""

import re
from typing import List, Optional
from fastapi import HTTPException, status
from app.models import OCREngine


def validate_ocr_engine(engine: str) -> OCREngine:
    """Validate and convert OCR engine string to enum."""
    try:
        return OCREngine(engine.lower())
    except ValueError:
        valid_engines = [e.value for e in OCREngine]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OCR engine. Supported engines: {', '.join(valid_engines)}"
        )


def validate_languages(languages: List[str]) -> List[str]:
    """Validate language codes."""
    if not languages:
        return ['eng']  # Default to 'eng' for Tesseract
    
    # Language code mapping for Tesseract compatibility
    language_mapping = {
        'en': 'eng',
        'english': 'eng',
        'fr': 'fra',
        'french': 'fra',
        'de': 'deu',
        'german': 'deu',
        'es': 'spa',
        'spanish': 'spa',
        'it': 'ita',
        'italian': 'ita',
        'pt': 'por',
        'portuguese': 'por'
    }
    
    # Basic validation - ensure language codes are reasonable
    valid_languages = []
    for lang in languages:
        if isinstance(lang, str) and len(lang.strip()) >= 2:
            lang_clean = lang.strip().lower()
            # Map common codes to Tesseract format
            mapped_lang = language_mapping.get(lang_clean, lang_clean)
            valid_languages.append(mapped_lang)
    
    return valid_languages if valid_languages else ['eng']


def validate_confidence_threshold(threshold: float) -> float:
    """Validate confidence threshold value."""
    if not (0.0 <= threshold <= 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confidence threshold must be between 0.0 and 1.0"
        )
    return threshold


def validate_request_id(request_id: str) -> str:
    """Validate request ID format."""
    # UUID v4 format validation
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    
    if not re.match(uuid_pattern, request_id.lower()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format"
        )
    
    return request_id.lower()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Remove any path separators and dangerous characters
    safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Limit length
    if len(safe_chars) > 255:
        name, ext = safe_chars.rsplit('.', 1) if '.' in safe_chars else (safe_chars, '')
        safe_chars = name[:250] + ('.' + ext if ext else '')
    
    return safe_chars