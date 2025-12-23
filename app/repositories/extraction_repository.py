"""Repository for managing extraction history and results."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
from loguru import logger

from app.models import TextExtractionResponse


class ExtractionRepository:
    """Repository for managing text extraction history."""
    
    def __init__(self, storage_dir: str = "logs/extractions"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
    
    async def save_extraction_result(self, extraction_response: TextExtractionResponse) -> bool:
        """Save extraction result to storage."""
        try:
            filename = f"{extraction_response.request_id}.json"
            filepath = os.path.join(self.storage_dir, filename)
            
            # Convert to dict for JSON serialization
            data = {
                'request_id': extraction_response.request_id,
                'result': {
                    'success': extraction_response.result.success,
                    'extracted_text': extraction_response.result.extracted_text,
                    'confidence_score': extraction_response.result.confidence_score,
                    'language_detected': extraction_response.result.language_detected,
                    'processing_time': extraction_response.result.processing_time,
                    'text_regions_count': len(extraction_response.result.text_regions)
                },
                'metadata': extraction_response.metadata,
                'timestamp': extraction_response.timestamp.isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Extraction result saved: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving extraction result: {str(e)}")
            return False
    
    async def get_extraction_by_id(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve extraction result by request ID."""
        try:
            filename = f"{request_id}.json"
            filepath = os.path.join(self.storage_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            logger.error(f"Error retrieving extraction result: {str(e)}")
            return None
    
    async def get_recent_extractions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent extraction results."""
        try:
            files = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.storage_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    files.append((filepath, mtime))
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for filepath, _ in files[:limit]:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        results.append(data)
                except Exception as e:
                    logger.error(f"Error reading file {filepath}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent extractions: {str(e)}")
            return []
    
    async def get_extraction_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        try:
            stats = {
                'total_extractions': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
                'average_confidence': 0.0,
                'average_processing_time': 0.0,
                'most_used_engine': 'unknown',
                'languages_detected': {},
                'recent_activity': {
                    'last_24h': 0,
                    'last_7d': 0,
                    'last_30d': 0
                }
            }
            
            if not os.path.exists(self.storage_dir):
                return stats
            
            now = datetime.utcnow()
            confidence_scores = []
            processing_times = []
            engines = {}
            languages = {}
            
            for filename in os.listdir(self.storage_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Basic counts
                    stats['total_extractions'] += 1
                    
                    if data['result']['success']:
                        stats['successful_extractions'] += 1
                        confidence_scores.append(data['result']['confidence_score'])
                        processing_times.append(data['result']['processing_time'])
                    else:
                        stats['failed_extractions'] += 1
                    
                    # Engine usage
                    engine = data['metadata'].get('ocr_engine', 'unknown')
                    engines[engine] = engines.get(engine, 0) + 1
                    
                    # Language detection
                    lang = data['result'].get('language_detected', 'unknown')
                    languages[lang] = languages.get(lang, 0) + 1
                    
                    # Recent activity
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                    if (now - timestamp).days < 1:
                        stats['recent_activity']['last_24h'] += 1
                    if (now - timestamp).days < 7:
                        stats['recent_activity']['last_7d'] += 1
                    if (now - timestamp).days < 30:
                        stats['recent_activity']['last_30d'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing stats file {filepath}: {str(e)}")
            
            # Calculate averages
            if confidence_scores:
                stats['average_confidence'] = sum(confidence_scores) / len(confidence_scores)
            if processing_times:
                stats['average_processing_time'] = sum(processing_times) / len(processing_times)
            
            # Most used engine
            if engines:
                stats['most_used_engine'] = max(engines.items(), key=lambda x: x[1])[0]
            
            # Languages detected
            stats['languages_detected'] = languages
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating extraction stats: {str(e)}")
            return stats
    
    async def cleanup_old_results(self, days_to_keep: int = 30) -> int:
        """Clean up old extraction results."""
        try:
            if not os.path.exists(self.storage_dir):
                return 0
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            cleaned_count = 0
            
            for filename in os.listdir(self.storage_dir):
                if not filename.endswith('.json'):
                    continue
                
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if mtime < cutoff_date:
                        os.remove(filepath)
                        cleaned_count += 1
                        logger.info(f"Cleaned up old extraction result: {filename}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning up file {filepath}: {str(e)}")
            
            logger.info(f"Cleanup completed. Removed {cleaned_count} old files.")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0