"""
Text Chunker Module
------------------
This module handles text chunking and sentence splitting with enhanced accuracy
and configurable chunk sizes.
"""

import re
import logging
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChunkConfig:
    """Configuration for text chunking."""
    min_sentence_length: int = 10
    max_sentence_length: int = 500
    min_words_per_sentence: int = 3
    max_words_per_sentence: int = 50
    default_chunk_size: int = 2

class TextChunker:
    """Handles text chunking and sentence splitting operations with enhanced accuracy."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """
        Initialize TextChunker with optional configuration.
        
        Args:
            config (Optional[ChunkConfig]): Configuration for chunking behavior
        """
        self.config = config or ChunkConfig()
        self.chunk_size = self.config.default_chunk_size
        
        # Common abbreviations that shouldn't split sentences
        self._abbreviations = {
            'mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sr.', 'jr.', 'ph.d.',
            'etc.', 'i.e.', 'e.g.', 'vs.', 'v.', 'fig.', 'st.', 'ave.',
            'inc.', 'ltd.', 'co.', 'corp.', 'pts.', 'vol.', 'rev.',
            'a.m.', 'p.m.', 'u.s.', 'u.k.', 'u.n.'
        }
        
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences with improved accuracy and abbreviation handling.
        
        Args:
            text (str): Input text to split into sentences
            
        Returns:
            List[str]: List of validated sentences
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")
            
        try:
            # Protect abbreviations
            protected_text = self._protect_abbreviations(text)
            
            # Split on sentence boundaries with improved regex
            sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])(?=\s*["""\'']?\s*[A-Z])'
            sentences = re.split(sentence_pattern, protected_text)
            
            # Restore abbreviations and clean sentences
            sentences = [self._restore_abbreviations(s.strip()) for s in sentences]
            
            # Filter and validate sentences
            valid_sentences = []
            for sentence in sentences:
                if self._is_valid_sentence(sentence):
                    valid_sentences.append(sentence)
                else:
                    logger.debug(f"Filtered invalid sentence: {sentence[:50]}...")
                    
            if not valid_sentences:
                raise ValueError("No valid sentences found in text")
                
            return valid_sentences
            
        except Exception as e:
            logger.error(f"Sentence splitting failed: {str(e)}")
            raise
    
    def create_chunks(self, sentences: List[str], chunk_size: Optional[int] = None) -> List[Dict[str, Union[str, None]]]:
        """
        Create chunks of specified size from sentences with metadata.
        
        Args:
            sentences (List[str]): List of sentences to chunk
            chunk_size (Optional[int]): Override default chunk size
            
        Returns:
            List[Dict[str, Union[str, None]]]: List of chunk dictionaries with metadata
            
        Raises:
            ValueError: If sentences list is empty or chunk size invalid
        """
        if not sentences:
            raise ValueError("Sentences list cannot be empty")
            
        if chunk_size is not None:
            if chunk_size < 1:
                raise ValueError("Chunk size must be positive")
            self.chunk_size = chunk_size
            
        chunks = []
        try:
            for i in range(0, len(sentences), self.chunk_size):
                chunk_sentences = sentences[i:i + self.chunk_size]
                
                # Only create chunk if we have enough sentences or it's the last chunk
                if len(chunk_sentences) == self.chunk_size or (i + self.chunk_size >= len(sentences)):
                    chunk_text = ' '.join(chunk_sentences)
                    chunks.append({
                        'text': chunk_text,
                        'image_url': None,
                        'audio_url': None,
                        'metadata': {
                            'sentence_count': len(chunk_sentences),
                            'word_count': len(chunk_text.split()),
                            'char_count': len(chunk_text)
                        }
                    })
                    
            logger.info(f"Created {len(chunks)} chunks from {len(sentences)} sentences")
            return chunks
            
        except Exception as e:
            logger.error(f"Chunk creation failed: {str(e)}")
            raise
    
    def _protect_abbreviations(self, text: str) -> str:
        """Replace periods in abbreviations with temporary markers."""
        protected_text = text
        for abbr in self._abbreviations:
            protected_text = re.sub(
                rf'\b{abbr[:-1]}\.',
                lambda m: m.group().replace('.', '<POINT>'),
                protected_text,
                flags=re.IGNORECASE
            )
        return protected_text
    
    def _restore_abbreviations(self, text: str) -> str:
        """Restore periods in abbreviations."""
        return text.replace('<POINT>', '.')
    
    def _is_valid_sentence(self, text: str) -> bool:
        """
        Enhanced sentence validation with configurable limits.
        
        Args:
            text (str): Sentence to validate
            
        Returns:
            bool: True if sentence is valid, False otherwise
        """
        if not text or len(text) < self.config.min_sentence_length:
            return False
            
        if len(text) > self.config.max_sentence_length:
            return False
            
        # Check for proper capitalization and ending
        if not re.match(r'^[A-Z].*[.!?]$', text.strip()):
            return False
            
        # Check word count
        word_count = len(text.split())
        if word_count < self.config.min_words_per_sentence:
            return False
            
        if word_count > self.config.max_words_per_sentence:
            return False
            
        # Check for balanced quotes and parentheses
        if text.count('"') % 2 != 0 or text.count('(') != text.count(')'):
            return False
            
        return True
