import os
import re
import uuid
import logging
import ebooklib
from ebooklib import epub
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
import PyPDF2
from bs4 import BeautifulSoup
from database import db
from models import TempBookData

logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_paragraphs = 5000
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Remove UTF-8 BOM if present
        text = text.replace('\ufeff', '')
        return text.strip()
        
    def _extract_title(self, text: str) -> str:
        """Extract main title from the text while avoiding chapter titles."""
        # Remove table of contents section
        text = re.sub(r'(?i)^\s*(?:table of )?contents\s*(?:\n|$).*?(?=\n\s*\n|\Z)', '', text, flags=re.DOTALL|re.MULTILINE)
        
        # Patterns for actual book titles, ordered by reliability
        title_patterns = [
            # Explicit title markers
            r'(?i)^[\s\*]*(?:Title|Book Title):\s*([^\n\.]+)(?:\n|$)',
            # Standalone capitalized text at start
            r'^\s*([A-Z][^a-z\n]{2,}(?:[A-Z\s\d&,\'-]){3,})(?:\n|$)',
            # First line if properly formatted
            r'^\s*([^\n]{5,100})(?:\n|$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text.strip(), re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Validate title format
                if self._is_valid_title(title):
                    return title
        
        return "Untitled Story"
        
    def _is_valid_title(self, title: str) -> bool:
        """Validate if extracted text is likely a proper title."""
        # Remove common invalid patterns
        if re.search(r'(?i)(chapter|section|part|volume|book)\s+\d+', title):
            return False
            
        # Check length and word count
        if len(title) < 3 or len(title) > 100:
            return False
            
        words = title.split()
        if len(words) < 1 or len(words) > 15:
            return False
            
        # Check for proper capitalization
        if not any(c.isupper() for c in title):
            return False
            
        return True
        
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
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

    def _is_valid_sentence(self, text: str) -> bool:
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

    def _process_section(self, section: Dict) -> List[Dict]:
        """Process a section of chunks for display."""
        if not section or 'chunks' not in section:
            logger.warning("Invalid section data format")
            return []
        
        chunks = section.get('chunks', [])
        if not chunks:
            logger.warning("No chunks found in section")
            return []
            
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
                chunks = self._create_chunks(sentences)

                # Add title chunk if valid
                if title != "Untitled Story":
                    chunks.insert(0, {
                        'text': f"Title: {title}",
                        'image_url': None,
                        'audio_url': None,
                        'is_title': True
                    })

                temp_id = str(uuid.uuid4())
                # Separate title from content chunks
                content_chunks = chunks[1:] if chunks and chunks[0].get('is_title') else chunks
                
                # Create a dedicated title section
                title_section = {
                    'title': 'Book Title',
                    'chunks': [{
                        'text': title,
                        'image_url': None,
                        'audio_url': None,
                        'is_title': True
                    }],
                    'index': 0,
                    'processed': True
                }
                
                # Create content section
                content_section = {
                    'title': 'Story Content',
                    'chunks': content_chunks,
                    'index': 1,
                    'processed': False
                }
                
                story_data = {
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(content_chunks),
                    'current_chunk': 0,
                    'created_at': str(datetime.utcnow()),
                    'sections': [title_section, content_section]
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
                    'chunks_per_page': 50
                }

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def get_next_section(self, temp_id: str, page: int = 1, chunks_per_page: int = 50) -> Optional[Dict]:
        """Get chunks for the specified page with pagination."""
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data or not temp_data.data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return None

        book_data = temp_data.data
        sections = book_data.get('sections', [])
        
        if not sections or len(sections) < 2:
            logger.error(f"Invalid sections data for ID: {temp_id}")
            return None
            
        # Always include title section
        title_section = sections[0]
        title_chunks = title_section.get('chunks', [])
        
        # Get content chunks from second section
        content_section = sections[1]
        content_chunks = content_section.get('chunks', [])

        total_content_chunks = len(content_chunks)
        start_idx = (page - 1) * chunks_per_page
        end_idx = min(start_idx + chunks_per_page, total_content_chunks)

        if start_idx >= total_content_chunks:
            logger.warning(f"Requested page {page} exceeds available chunks")
            return None

        # Get content chunks for current page
        current_chunks = content_chunks[start_idx:end_idx]
        
        # Always include title chunks at the beginning of first page
        if page == 1:
            current_chunks = title_chunks + current_chunks
        
        logger.info(f"Serving page {page}/{(total_content_chunks + chunks_per_page - 1) // chunks_per_page}")
        
        return {
            'chunks': current_chunks,
            'current_page': page,
            'total_pages': (total_content_chunks + chunks_per_page - 1) // chunks_per_page,
            'has_next': end_idx < total_content_chunks,
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