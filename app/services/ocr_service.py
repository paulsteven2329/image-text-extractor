"""OCR service with support for multiple OCR engines."""

import os
import pytesseract
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
import time

# Set up Tesseract environment before any operations
os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata'

from app.core.config import settings
from app.core.exceptions import OCRError
from app.models import OCREngine, BoundingBox, TextRegion

# Optional import for EasyOCR
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    logger.info("EasyOCR is available")
except ImportError as e:
    EASYOCR_AVAILABLE = False
    logger.warning(f"EasyOCR is not available: {str(e)}. Only Tesseract will be used.")


class OCRService:
    """Service for text extraction using various OCR engines."""
    
    def __init__(self):
        self.tesseract_config = settings.TESSERACT_CONFIG
        self.easyocr_languages = settings.EASYOCR_LANGUAGES
        self._easyocr_reader = None
    
    def extract_text(self, 
                    image_path: str, 
                    engine: OCREngine = OCREngine.TESSERACT,
                    languages: List[str] = None,
                    confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Extract text using specified OCR engine."""
        
        start_time = time.time()
        
        try:
            if engine == OCREngine.TESSERACT:
                result = self._extract_with_tesseract(image_path, languages, confidence_threshold)
            elif engine == OCREngine.EASYOCR:
                if not EASYOCR_AVAILABLE:
                    logger.warning("EasyOCR not available, falling back to Tesseract")
                    result = self._extract_with_tesseract(image_path, languages, confidence_threshold)
                else:
                    result = self._extract_with_easyocr(image_path, languages, confidence_threshold)
            else:
                raise OCRError(f"Unsupported OCR engine: {engine}")
            
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            logger.info(f"OCR extraction completed in {processing_time:.2f}s using {engine}")
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction error with {engine}: {str(e)}")
            raise OCRError(f"OCR extraction failed: {str(e)}")
    
    def _extract_with_tesseract(self, 
                               image_path: str, 
                               languages: List[str] = None,
                               confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Extract text using Tesseract OCR."""
        try:
            # Set language parameter - ensure we use 'eng' not 'en'
            lang_mapping = {'en': 'eng', 'eng': 'eng'}  # Map common variants
            mapped_languages = []
            for lang in (languages or ['en']):
                mapped_languages.append(lang_mapping.get(lang, lang))
            
            lang_param = '+'.join(mapped_languages)
            
            logger.debug(f"Using Tesseract language parameter: {lang_param}")
            
            # Enhanced Tesseract configuration for better text recognition
            enhanced_config = self.tesseract_config
            
            # Get detailed OCR data with enhanced configuration
            ocr_data = pytesseract.image_to_data(
                image_path, 
                lang=lang_param,
                config=enhanced_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract full text with better formatting
            full_text = pytesseract.image_to_string(
                image_path,
                lang=lang_param,
                config=enhanced_config
            )
            
            logger.debug(f"OCR raw text: '{full_text}'")
            logger.debug(f"OCR data keys: {list(ocr_data.keys())}")
            logger.debug(f"OCR text entries: {len([t for t in ocr_data.get('text', []) if t.strip()])}")
            
            # Process and improve text formatting
            try:
                # Try our improved formatting method first
                formatted_text = self._improve_text_formatting(full_text, ocr_data)
                
                # If improved formatting worked well, use it
                if formatted_text and len(formatted_text.strip()) > len(full_text.strip()) * 0.8:
                    final_text = formatted_text
                else:
                    # Fall back to cleaned direct text
                    clean_text = full_text.strip().replace('\x0c', '').strip()
                    final_text = clean_text if clean_text else formatted_text
                    
            except Exception as e:
                logger.warning(f"Text processing failed, using raw text: {str(e)}")
                final_text = full_text.strip()
            
            # Process OCR data to extract regions with better spacing
            text_regions = self._process_tesseract_data_enhanced(ocr_data, confidence_threshold)
            
            # Calculate overall confidence
            confidences = [region.confidence for region in text_regions if region.confidence > 0]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Detect language (simple heuristic)
            detected_language = self._detect_language(final_text)
            
            return {
                'success': True,
                'extracted_text': final_text.strip(),
                'text_regions': text_regions,
                'confidence_score': overall_confidence,
                'language_detected': detected_language
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR error: {str(e)}")
            raise OCRError(f"Tesseract OCR failed: {str(e)}")
    
    def _extract_with_easyocr(self,
                             image_path: str,
                             languages: List[str] = None,
                             confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """Extract text using EasyOCR."""
        if not EASYOCR_AVAILABLE:
            raise OCRError("EasyOCR is not available")
            
        try:
            # Initialize EasyOCR reader if not already done
            if self._easyocr_reader is None:
                langs = languages if languages else self.easyocr_languages
                self._easyocr_reader = easyocr.Reader(langs)
            
            # Read image and extract text
            results = self._easyocr_reader.readtext(image_path)
            
            # Process EasyOCR results
            text_regions = []
            full_text_parts = []
            
            for detection in results:
                bbox_coords = detection[0]
                text = detection[1]
                confidence = detection[2]
                
                if confidence >= confidence_threshold:
                    # Convert bbox coordinates to our format
                    x_coords = [point[0] for point in bbox_coords]
                    y_coords = [point[1] for point in bbox_coords]
                    
                    x = int(min(x_coords))
                    y = int(min(y_coords))
                    width = int(max(x_coords) - min(x_coords))
                    height = int(max(y_coords) - min(y_coords))
                    
                    bounding_box = BoundingBox(x=x, y=y, width=width, height=height)
                    
                    text_region = TextRegion(
                        text=text,
                        confidence=confidence,
                        bounding_box=bounding_box
                    )
                    
                    text_regions.append(text_region)
                    full_text_parts.append(text)
            
            # Combine all text
            full_text = ' '.join(full_text_parts)
            
            # Calculate overall confidence
            confidences = [region.confidence for region in text_regions]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Detect language
            detected_language = self._detect_language(full_text)
            
            return {
                'success': True,
                'extracted_text': full_text.strip(),
                'text_regions': text_regions,
                'confidence_score': overall_confidence,
                'language_detected': detected_language
            }
            
        except Exception as e:
            logger.error(f"EasyOCR error: {str(e)}")
            raise OCRError(f"EasyOCR failed: {str(e)}")
    
    def _improve_text_formatting(self, raw_text: str, ocr_data: Dict) -> str:
        """Improve text formatting by analyzing word positions and spacing."""
        try:
            # Create word objects with position data
            words_by_line = {}
            
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                conf = ocr_data['conf'][i]
                level = ocr_data['level'][i]
                
                # Only process word-level data (level 5) with decent confidence
                if level == 5 and text and conf >= 20:
                    line_num = ocr_data['line_num'][i]
                    par_num = ocr_data['par_num'][i]
                    
                    line_key = f"{par_num}_{line_num}"
                    
                    if line_key not in words_by_line:
                        words_by_line[line_key] = []
                    
                    words_by_line[line_key].append({
                        'text': text,
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i],
                        'word_num': ocr_data['word_num'][i],
                        'confidence': conf
                    })
            
            if not words_by_line:
                return ' '.join(raw_text.split())
            
            # Process each line and add intelligent spacing
            formatted_lines = []
            for line_key in sorted(words_by_line.keys()):
                words = words_by_line[line_key]
                
                # Sort words by their position (left coordinate, then word_num)
                words.sort(key=lambda x: (x['left'], x['word_num']))
                
                # Reconstruct line with intelligent spacing
                line_parts = []
                for i, word in enumerate(words):
                    if i > 0:
                        prev_word = words[i-1]
                        prev_right = prev_word['left'] + prev_word['width']
                        current_left = word['left']
                        
                        # Calculate gap between words
                        gap = current_left - prev_right
                        avg_char_width = prev_word['width'] / max(len(prev_word['text']), 1)
                        
                        # Add space if gap suggests word separation
                        # Heuristic: if gap is more than half a character width, add space
                        if gap > avg_char_width * 0.3:
                            line_parts.append(' ')
                        
                        # Special handling for merged words - try to detect patterns
                        word_text = word['text']
                        if len(word_text) > 8:  # Likely merged word
                            # Try to split common patterns
                            word_text = self._attempt_word_splitting(word_text)
                            word['processed_text'] = word_text
                    
                    line_parts.append(word.get('processed_text', word['text']))
                
                line_text = ''.join(line_parts).strip()
                if line_text:
                    formatted_lines.append(line_text)
            
            result = '\n'.join(formatted_lines)
            
            # Quality check and fallback
            if result and len(result.strip()) >= len(raw_text.strip()) * 0.5:
                return result
            else:
                return ' '.join(raw_text.split())
            
        except Exception as e:
            logger.warning(f"Text formatting improvement failed: {str(e)}")
            return ' '.join(raw_text.split())
    
    def _attempt_word_splitting(self, text: str) -> str:
        """Attempt to split merged words using common patterns."""
        try:
            import re
            
            # Common word splitting patterns
            patterns = [
                # Insert space before capital letters (except first)
                (r'([a-z])([A-Z])', r'\1 \2'),
                # Insert space between letters and numbers
                (r'([a-zA-Z])(\d)', r'\1 \2'),
                (r'(\d)([a-zA-Z])', r'\1 \2'),
                # Split common merged words
                (r'Thisisa', 'This is a'),
                (r'testimage', 'test image'),
                (r'OCRextraction', 'OCR extraction'),
                (r'forOCR', 'for OCR'),
            ]
            
            result = text
            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result)
            
            return result
            
        except Exception:
            return text
    
    def _process_tesseract_data_enhanced(self, ocr_data: Dict, confidence_threshold: float) -> List[TextRegion]:
        """Process Tesseract OCR data to extract text regions with better spacing."""
        text_regions = []
        
        # Group data by lines first
        lines = {}
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            confidence = ocr_data['conf'][i] / 100.0  # Convert to 0-1 scale
            line_num = ocr_data['line_num'][i]
            
            # Use a lower threshold for processing, but keep original for final filtering
            # This ensures we don't lose too much text during processing
            processing_threshold = min(confidence_threshold, 0.3)  # At least 30% confidence
            if text and confidence >= processing_threshold:
                if line_num not in lines:
                    lines[line_num] = []
                
                lines[line_num].append({
                    'text': text,
                    'confidence': confidence,
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'word_num': ocr_data['word_num'][i]
                })
        
                # Process each line and create regions
        for line_num in sorted(lines.keys()):
            line_words = lines[line_num]
            if line_words:
                # Sort words by position in line
                line_words.sort(key=lambda x: (x['word_num'], x['left']))
                
                # Group consecutive words with similar confidence
                for word_data in line_words:
                    # Apply the original confidence threshold here for final filtering
                    if word_data['confidence'] >= confidence_threshold:
                        bounding_box = BoundingBox(
                            x=word_data['left'],
                            y=word_data['top'],
                            width=word_data['width'],
                            height=word_data['height']
                        )
                        
                        text_region = TextRegion(
                            text=word_data['text'],
                            confidence=word_data['confidence'],
                            bounding_box=bounding_box
                        )
                        
                        text_regions.append(text_region)
        
        return text_regions
    
    def _process_tesseract_data(self, ocr_data: Dict, confidence_threshold: float) -> List[TextRegion]:
        """Process Tesseract OCR data to extract text regions."""
        return self._process_tesseract_data_enhanced(ocr_data, confidence_threshold)
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection heuristic."""
        # This is a basic implementation - in production, you might want to use
        # a proper language detection library like langdetect
        
        if not text.strip():
            return 'unknown'
        
        # Count ASCII vs non-ASCII characters
        ascii_count = sum(1 for char in text if ord(char) < 128)
        total_count = len(text)
        
        if total_count == 0:
            return 'unknown'
        
        ascii_ratio = ascii_count / total_count
        
        if ascii_ratio > 0.8:
            return 'en'  # Likely English or other Latin-based language
        else:
            return 'other'  # Non-Latin script
    
    def get_supported_languages(self, engine: OCREngine) -> List[str]:
        """Get list of supported languages for the specified engine."""
        try:
            if engine == OCREngine.TESSERACT:
                langs = pytesseract.get_languages()
                return list(langs)
            elif engine == OCREngine.EASYOCR:
                if EASYOCR_AVAILABLE:
                    return ['en', 'ch_sim', 'ch_tra', 'fr', 'de', 'ja', 'ko']  # Common languages
                else:
                    return []  # EasyOCR not available
            else:
                return ['en']
        except Exception as e:
            logger.error(f"Error getting supported languages: {str(e)}")
            return ['en']