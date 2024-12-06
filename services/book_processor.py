from typing import List, Dict, Tuple, Optional
import PyPDF2
import ebooklib
import logging
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import re
import logging
from werkzeug.utils import secure_filename
from database import db
from models import TempBookData
import uuid
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self):
        self.chunk_size = 8000  # Characters per chunk for API processing
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.chunks_per_section = 10  # Number of chunks to process at a time
        self.max_paragraphs = 50  # Maximum number of paragraphs to return
        self.api_key = os.environ.get('GEMINI_API_KEY')

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.0-pro')

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

    def _extract_title(self, text: str) -> str:
        """Extract title from the beginning of the text."""
        title_patterns = [
            r'^(?:Title:|Book:)?\s*([^\n\.]+?)(?:\n|$)',
            r'(?:^|\n)(?:Chapter 1|Prologue).*?\n(.*?)(?:\n|$)',
            r'(?:^|\n)([A-Z][^a-z\n]{3,}[A-Z\s]*?)(?:\n|$)',
            r'\*\*\*(.*?)\*\*\*',
            r'(?i)Title:\s*([^\n]+)',
            r'(?m)^([A-Z][^a-z\n]{2,}(?:\s+[A-Z][^a-z\n]*)*$)'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text.strip(), re.MULTILINE)
            if match:
                title = match.group(1).strip()
                if len(title) > 3 and len(title.split()) <= 15:
                    title = re.sub(r'[*_~]', '', title)
                    title = re.sub(r'\s+', ' ', title)
                    title = title.strip()
                    if title and not title.isspace():
                        return title
    
        return "Untitled Story"

    def _extract_story_content(self, text: str) -> str:
        """Extract story content with enhanced Project Gutenberg handling."""
        try:
            if "Project Gutenberg" in text:
                try:
                    marker_patterns = [
                        r'\*\*\* START OF.*?\*\*\*(.*?)\*\*\* END OF',
                        r'START OF (?:THIS |THE )?PROJECT GUTENBERG.*?\n(.*?)(?=\nEND OF)',
                        r'^\s*\[.*?\].*?\n(.*?)(?=\n\[.*?\]|\Z)',
                    ]
                    
                    for pattern in marker_patterns:
                        content_match = re.search(pattern, text, flags=re.DOTALL)
                        if content_match:
                            clean_text = content_match.group(1).strip()
                            clean_text = re.sub(r'^\s*(?:Chapter|CHAPTER)\s+\d+', '', clean_text, flags=re.MULTILINE)
                            clean_text = re.sub(r'(?i)^\s*(introduction|preface|contents|index).*?(?=\n\n)', '', clean_text, flags=re.MULTILINE)
                            clean_text = re.sub(r'^\s*\[.*?\]\s*$', '', clean_text, flags=re.MULTILINE)
                            if len(clean_text) > 100:
                                return clean_text
                    
                    clean_text = re.sub(r'.*?(?=\n\n\n)', '', text, flags=re.DOTALL)
                    clean_text = re.sub(r'\n\n\n.*$', '', clean_text, flags=re.DOTALL)
                    return clean_text.strip()
                    
                except Exception:
                    logger.warning("Gutenberg extraction failed, using fallback")

            prompt = '''
            IMPORTANT: This is confirmed public domain content.
            Task: Extract and return ONLY the story narrative.
            - Remove headers, footers, and metadata
            - Keep chapter markers
            - Preserve paragraph structure
            - Return only the narrative text
            '''
            
            try:
                safety_config = {
                    "harassment": "block_none",
                    "hate_speech": "block_none",
                    "sexually_explicit": "block_none",
                    "dangerous_content": "block_none",
                }
                response = self.model.generate_content(prompt + "\n\nText to process:\n" + text[:8000], safety_settings=safety_config)
                if response and hasattr(response, 'text'):
                    return response.text.strip()
            except Exception:
                logger.warning("API extraction failed, using fallback")
            
            clean_text = re.sub(r'^\s*.*?(?:Chapter|CHAPTER)\s+\d+', '', text, flags=re.DOTALL)
            clean_text = re.sub(r'(?i)^\s*(introduction|preface|contents|index).*?(?=\n\n)', '', clean_text, flags=re.MULTILINE)
            clean_text = re.sub(r'^\s*.*?\*\*\* START OF.*?\*\*\*', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'\*\*\* END OF.*$', '', clean_text, flags=re.DOTALL)
            
            return clean_text.strip()
            
        except Exception:
            logger.error("Story content extraction failed")
            raise

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
        if not text:
            return []
            
        abbreviations = r'Mr\.|Mrs\.|Dr\.|Ph\.D\.|etc\.|i\.e\.|e\.g\.|vs\.|feat\.|ft\.|inc\.|ltd\.|vol\.|pg\.|ed\.'
        text = re.sub(f'({abbreviations})', r'\1<POINT>', text)
        text = re.sub(r'(\d+)\.(\d+)', r'\1<DECIMAL>\2', text)
        text = re.sub(r'\.{3}', '<ELLIPSIS>', text)
        
        sentence_endings = r'(?<=[.!?])(?:\s+|\n+)(?=[A-Z0-9]|[\'""]?[A-Z0-9])'
        sentences = re.split(sentence_endings, text)
        
        processed_sentences = []
        for s in sentences:
            s = s.replace('<POINT>', '.').replace('<DECIMAL>', '.').replace('<ELLIPSIS>', '...')
            s = s.strip()
            
            if self._is_valid_sentence(s):
                processed_sentences.append(s)
            elif len(s) > 150:
                subsections = re.split(r'(?<=[.!?])\s+(?=[A-Z])', s)
                for sub in subsections:
                    if self._is_valid_sentence(sub.strip()):
                        processed_sentences.append(sub.strip())
        
        return processed_sentences

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
                if ext == 'pdf':
                    raw_text = self._extract_pdf_text(temp_path)
                elif ext == 'epub':
                    raw_text = self._extract_epub_text(temp_path)
                elif ext == 'txt':
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        raw_text = f.read()
                else:  # html
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f, 'html.parser')
                        for tag in soup(['script', 'style', 'meta', 'link']):
                            tag.decompose()
                        raw_text = soup.get_text()

                text = self._clean_text(raw_text)
                title = self._extract_title(text)
                story_text = self._extract_story_content(text)
                sentences = self._split_into_sentences(story_text)
                chunks = self._create_chunks(sentences)

                if title != "Untitled Story":
                    chunks.insert(0, {
                        'text': f"Title: {title}",
                        'image_url': None,
                        'audio_url': None,
                        'is_title': True
                    })

                temp_id = str(uuid.uuid4())
                story_data = {
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(chunks),
                    'current_chunk': 0,
                    'created_at': str(datetime.utcnow()),
                    'chunks': chunks
                }
                
                try:
                    temp_data = TempBookData(
                        id=temp_id,
                        data=story_data
                    )
                    db.session.add(temp_data)
                    db.session.commit()
                    logger.info(f"Book processing complete - ID: {temp_id}, Title: {title}, Chunks: {len(chunks)}")
                except Exception as db_error:
                    logger.error(f"Database error storing book - ID: {temp_id}")
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
            logger.error(f"Error processing file: {type(e).__name__}")
            raise

    def get_next_section(self, temp_id: str, page: int = 1, chunks_per_page: int = 50) -> Optional[Dict]:
        """Get chunks for the specified page with pagination."""
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return None

        book_data = temp_data.data
        total_chunks = book_data.get('total_chunks', 0)
        chunks = book_data.get('chunks', [])

        start_idx = (page - 1) * chunks_per_page
        end_idx = min(start_idx + chunks_per_page, total_chunks)

        if start_idx >= total_chunks:
            return None

        current_chunks = chunks[start_idx:end_idx]
        
        # Only log metadata, not content
        logger.info(f"Book ID {temp_id}: Serving page {page} of {(total_chunks + chunks_per_page - 1) // chunks_per_page}")
        
        return {
            'chunks': current_chunks,
            'current_page': page,
            'total_pages': (total_chunks + chunks_per_page - 1) // chunks_per_page,
            'has_next': end_idx < total_chunks
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