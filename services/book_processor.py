from typing import List, Dict, Optional
import re
import os
import logging
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from models import TempBookData
from database import db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self, chunk_size=10, max_file_size=50*1024*1024):
        self.chunk_size = chunk_size
        self.max_file_size = max_file_size

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
            
        # Replace multiple newlines with single newline
        text = re.sub(r'\n\s*\n', '\n', text)
        # Remove excess whitespace
        text = re.sub(r'\s+', ' ', text)
        # Clean up punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        
        return text.strip()

    def _extract_title(self, text: str) -> str:
        """Extract title from the beginning of the text."""
        try:
            # Look for common title patterns
            title_patterns = [
                r'^[A-Z][^.!?]*(?:[.!?]|$)',  # First sentence in all caps
                r'^(?:Title:|Chapter \d+:)?\s*([A-Z][^.!?]*?)(?:\n|$)',  # Title or Chapter prefix
                r'^([A-Z][A-Z\s]+)(?:\n|$)'  # All uppercase text at start
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text)
                if match:
                    title = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    return self._clean_text(title)
            
            # Fallback: use first line if no pattern matches
            first_line = text.split('\n')[0]
            return self._clean_text(first_line) or "Untitled"
            
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return "Untitled"

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if self._is_valid_sentence(s)]

    def _is_valid_sentence(self, text: str) -> bool:
        """Enhanced sentence validation."""
        if not text or len(text) < 10:  # Too short
            return False
            
        # Must start with capital letter and end with punctuation
        if not re.match(r'^[A-Z].*[.!?]$', text.strip()):
            return False
            
        # Must have reasonable word count
        word_count = len(text.split())
        if word_count < 3 or word_count > 50:  # Adjust thresholds as needed
            return False
            
        # Check for balanced quotes and parentheses
        if text.count('"') % 2 != 0 or text.count('(') != text.count(')'):
            return False
            
        return True

    def _process_section(self, section: Dict) -> List[Dict]:
        """Process a section of text into chunks."""
        try:
            # Get chunks from section
            chunks = section.get('chunks', [])
            if not chunks:
                logger.error("No chunks found in section")
                return []

            # Process each chunk if needed
            processed_chunks = []
            for chunk in chunks:
                if isinstance(chunk, dict) and 'text' in chunk:
                    processed_chunks.append({
                        'text': self._clean_text(chunk['text']),
                        'image_url': chunk.get('image_url'),
                        'audio_url': chunk.get('audio_url'),
                        'is_title': chunk.get('is_title', False)
                    })

            return processed_chunks
        except Exception as e:
            logger.error(f"Error processing section: {str(e)}")
            return []

    def _create_chunks(self, sentences: List[str], chunk_size: int = 2) -> List[Dict[str, str]]:
        """Create chunks of specified size from sentences."""
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk_sentences = sentences[i:i + chunk_size]
            if len(chunk_sentences) == chunk_size or (i + chunk_size >= len(sentences)):
                chunk_text = ' '.join(chunk_sentences)
                chunks.append({
                    'text': chunk_text,
                    'image_url': None,
                    'audio_url': None
                })
        return chunks

    def _extract_story_content(self, text: str) -> str:
        """Extract story content while removing table of contents and chapter headers."""
        try:
            # Remove table of contents
            clean_text = re.sub(r'(?i)^(?:table of )?contents\s*(?:\n|$).*?(?=\n\s*\n|\Z)', '', text, flags=re.DOTALL|re.MULTILINE)
            
            # Remove chapter headers and numbers
            clean_text = re.sub(r'(?i)^\s*(?:chapter|section|part|volume)\s+[IVXLCDM\d]+\.?\s*.*$', '', clean_text, flags=re.MULTILINE)
            
            # Remove common book sections
            clean_text = re.sub(r'(?i)^\s*(introduction|preface|foreword|appendix|index|bibliography).*?(?=\n\s*\n|\Z)', '', clean_text, flags=re.DOTALL|re.MULTILINE)
            
            # Remove Project Gutenberg headers and footers
            clean_text = re.sub(r'^\s*.*?\*\*\* START OF.*?\*\*\*.*?\n', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'\*\*\* END OF.*$', '', clean_text, flags=re.DOTALL)
            
            # Remove consecutive blank lines
            clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
            
            return clean_text.strip()
        except Exception:
            logger.error("Story content extraction failed")
            raise

    def process_file(self, file) -> Dict[str, any]:
        """Process uploaded file based on its type."""
        try:
            if not file:
                raise ValueError("No file provided")

            filename = secure_filename(file.filename)
            if not filename or '.' not in filename:
                raise ValueError("Invalid filename")

            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in {'pdf', 'epub', 'txt', 'html'}:
                raise ValueError(f"Unsupported file type: {ext}")

            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > self.max_file_size:
                raise ValueError(f"File too large. Maximum size is {self.max_file_size/(1024*1024)}MB")

            temp_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(temp_path)

            try:
                # Extract text based on file type
                if ext == 'pdf':
                    text = self._extract_pdf_text(temp_path)
                elif ext == 'epub':
                    text = self._extract_epub_text(temp_path)
                elif ext == 'txt':
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:  # html
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        for tag in soup(['script', 'style', 'meta', 'link']):
                            tag.decompose()
                        text = soup.get_text()

                # Process extracted text
                text = self._clean_text(text)
                title = self._extract_title(text)
                story_text = self._extract_story_content(text)
                sentences = self._split_into_sentences(story_text)
                chunks = self._create_chunks(sentences, chunk_size=2)

                # Store title and content chunks
                temp_id = str(uuid.uuid4())
                story_data = {
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(chunks),
                    'current_chunk': 0,
                    'created_at': str(datetime.utcnow()),
                    'sections': [{
                        'title': 'Story Content',
                        'chunks': chunks,
                        'index': 0,
                        'processed': False
                    }]
                }

                try:
                    temp_data = TempBookData(id=temp_id, data=story_data)
                    db.session.add(temp_data)
                    db.session.commit()
                    logger.info(f"Successfully processed book - ID: {temp_id}, Title: {title}")
                except Exception as db_error:
                    logger.error(f"Database error - ID: {temp_id}")
                    db.session.rollback()
                    raise

                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(chunks),
                    'current_page': 1,
                    'chunks_per_page': 10
                }

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def get_next_section(self, temp_id: str, page: int = 1, chunks_per_page: int = 10) -> Optional[Dict]:
        """Get chunks for the specified page with pagination."""
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data or not temp_data.data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return None

        book_data = temp_data.data
        sections = book_data.get('sections', [])
        
        if not sections:
            logger.error(f"No sections found in temp data")
            return None
            
        content_section = sections[0]
        content_chunks = content_section.get('chunks', [])
        total_chunks = len(content_chunks)
        
        # Calculate pagination
        start_idx = (page - 1) * chunks_per_page
        end_idx = min(start_idx + chunks_per_page, total_chunks)

        if start_idx >= total_chunks:
            logger.warning(f"Requested page {page} exceeds available chunks")
            return None

        current_chunks = content_chunks[start_idx:end_idx]
        logger.info(f"Serving page {page}/{(total_chunks + chunks_per_page - 1) // chunks_per_page}")
        
        return {
            'chunks': current_chunks,
            'current_page': page,
            'total_pages': (total_chunks + chunks_per_page - 1) // chunks_per_page,
            'has_next': end_idx < total_chunks,
            'title': book_data.get('title')
        }

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n".join(text)
        except Exception as e:
            logger.error("PDF extraction failed")
            raise

    def _extract_epub_text(self, epub_path: str) -> str:
        """Extract text from EPUB file."""
        text = []
        try:
            book = epub.read_epub(epub_path)
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    soup = BeautifulSoup(content, 'html.parser')
                    if soup.get_text():
                        text.append(soup.get_text())
            return "\n".join(text)
        except Exception as e:
            logger.error("EPUB extraction failed")
            raise
