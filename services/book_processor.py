from typing import List, Dict
import PyPDF2
import ebooklib
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self):
        self.chunk_size = 2  # Two sentences per chunk
        self.chunks_per_page = 10  # Number of chunks per page
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.api_key = os.environ.get('GEMINI_API_KEY')

        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')

    def process_file(self, file) -> Dict[str, any]:
        """Process uploaded file based on its type."""
        try:
            if not file:
                raise ValueError("No file provided")

            filename = secure_filename(file.filename)
            if not filename or '.' not in filename:
                raise ValueError("Invalid filename")

            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in {'pdf', 'epub', 'html'}:
                raise ValueError(f"Unsupported file type: {ext}")

            # Check file size
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > self.max_file_size:
                raise ValueError(f"File too large. Maximum size is {self.max_file_size/(1024*1024)}MB")

            # Create temporary file
            temp_path = os.path.join('uploads', filename)
            file.save(temp_path)

            try:
                if ext == 'pdf':
                    chunks = self.process_pdf(temp_path)
                elif ext == 'epub':
                    chunks = self.process_epub(temp_path)
                else:  # html
                    chunks = self.process_html(temp_path)

                # Store processed data in temporary storage
                temp_id = str(uuid.uuid4())
                temp_data = TempBookData(
                    id=temp_id,
                    data={
                        'source_file': filename,
                        'paragraphs': chunks,
                        'chunk_size': self.chunk_size,
                        'chunks_per_page': self.chunks_per_page,
                        'total_chunks': len(chunks)
                    }
                )
                db.session.add(temp_data)
                db.session.commit()

                # Return first page of data
                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'paragraphs': chunks[:self.chunks_per_page],
                    'total_chunks': len(chunks),
                    'current_page': 1,
                    'total_pages': (len(chunks) + self.chunks_per_page - 1) // self.chunks_per_page
                }

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def process_pdf(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from PDF files."""
        try:
            raw_text = self._extract_pdf_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def process_epub(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from EPUB files."""
        try:
            raw_text = self._extract_epub_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing EPUB: {str(e)}")
            raise

    def process_html(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from HTML files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                # Remove scripts, styles, and other non-content elements
                for tag in soup(['script', 'style', 'meta', 'link']):
                    tag.decompose()
                raw_text = soup.get_text()
                return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing HTML: {str(e)}")
            raise

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
            logger.error(f"Error extracting PDF text: {str(e)}")
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
            logger.error(f"Error extracting EPUB text: {str(e)}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove common metadata sections and formatting
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

    def _is_story_content(self, text: str) -> bool:
        """Check if text is story content rather than metadata or other non-story text."""
        # Check minimum length and sentence structure
        if len(text.split()) < 10:  # Skip very short segments
            return False

        # Ensure text has proper sentence structure
        if not re.search(r'[A-Z][^.!?]+[.!?]', text):
            return False

        return True

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Split text into sections (letters/chapters)
            section_pattern = r'(?:LETTER|CHAPTER)\s+[IVX0-9]+'
            sections = re.split(f'({section_pattern})', text)
            
            chunks = []
            current_section = None
            
            for i in range(len(sections)):
                if i % 2 == 0:  # Content
                    if not sections[i].strip():
                        continue
                        
                    # Split content into sentences
                    content = sections[i].strip()
                    sentences = re.split(r'(?<=[.!?])\s+', content)
                    sentences = [s.strip() for s in sentences if s.strip()]
                    
                    # Group sentences into chunks
                    for j in range(0, len(sentences), 2):
                        if j + 1 < len(sentences):
                            chunk_text = f"{sentences[j]} {sentences[j+1]}"
                        else:
                            chunk_text = sentences[j]
                            
                        if self._is_story_content(chunk_text):
                            chunks.append({
                                'text': chunk_text,
                                'image_url': None,
                                'audio_url': None,
                                'section': current_section
                            })
                            
                else:  # Section header
                    current_section = sections[i].strip()

            logger.info(f"Successfully processed {len(chunks)} two-sentence chunks")
            return chunks

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise