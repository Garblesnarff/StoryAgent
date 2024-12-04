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
        self.chunk_size = 8000  # Characters per chunk for API processing
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        self.max_paragraphs = 10  # Maximum number of paragraphs to process
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
                    paragraphs = self.process_pdf(temp_path)
                elif ext == 'epub':
                    paragraphs = self.process_epub(temp_path)
                else:  # html
                    paragraphs = self.process_html(temp_path)
                    
                # Store processed data in temporary storage
                temp_id = str(uuid.uuid4())
                temp_data = TempBookData(
                    id=temp_id,
                    data={
                        'source_file': filename,
                        'paragraphs': paragraphs
                    }
                )
                db.session.add(temp_data)
                db.session.commit()
                
                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'paragraphs': paragraphs
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


