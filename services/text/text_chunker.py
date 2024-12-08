import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TextChunker:
    """Handles text chunking and sentence splitting operations."""
    
    def __init__(self):
        self.chunk_size = 2  # Default chunk size
        
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
        try:
            # Handle common abbreviations
            abbreviations = r'Mr\.|Mrs\.|Dr\.|Ph\.D\.|etc\.|i\.e\.|e\.g\.'
            text = re.sub(f'({abbreviations})', r'\1<POINT>', text)
            
            # Split on sentence boundaries
            sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'
            sentences = re.split(sentence_endings, text)
            
            # Restore points and clean sentences
            sentences = [s.replace('<POINT>', '.').strip() for s in sentences]
            
            # Filter out invalid sentences
            return [s for s in sentences if self._is_valid_sentence(s)]
        except Exception as e:
            logger.error(f"Sentence splitting failed: {str(e)}")
            raise
    
    def create_chunks(self, sentences: List[str], chunk_size: int = None) -> List[Dict[str, str]]:
        """Create chunks of specified size from sentences."""
        if chunk_size is not None:
            self.chunk_size = chunk_size
            
        chunks = []
        try:
            for i in range(0, len(sentences), self.chunk_size):
                chunk_sentences = sentences[i:i + self.chunk_size]
                if len(chunk_sentences) == self.chunk_size or (i + self.chunk_size >= len(sentences)):
                    chunk_text = ' '.join(chunk_sentences)
                    chunks.append({
                        'text': chunk_text,
                        'image_url': None,
                        'audio_url': None
                    })
            return chunks
        except Exception as e:
            logger.error(f"Chunk creation failed: {str(e)}")
            raise
    
    @staticmethod
    def _is_valid_sentence(text: str) -> bool:
        """Enhanced sentence validation."""
        if not text or len(text) < 10:
            return False

        if not re.match(r'^[A-Z].*[.!?]$', text.strip()):
            return False

        word_count = len(text.split())
        if word_count < 3 or word_count > 50:
            return False

        if text.count('"') % 2 != 0 or text.count('(') != text.count(')'):
            return False

        return True
