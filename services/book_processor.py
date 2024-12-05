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
        self.model = genai.GenerativeModel('gemini-1.0-pro')

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove common metadata sections and formatting
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

    def _extract_title(self, text: str) -> str:
        """Extract title from the beginning of the text."""
        # Look for common title patterns
        title_patterns = [
            r'^(?:Title:|Book:)?\s*([^\n\.]+?)(?:\n|$)',  # Basic title at start
            r'(?:^|\n)(?:Chapter 1|Prologue).*?\n(.*?)(?:\n|$)',  # Title before first chapter
            r'(?:^|\n)([A-Z][^a-z\n]{3,}[A-Z\s]*?)(?:\n|$)'  # ALL CAPS title pattern
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text.strip(), re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Validate title
                if len(title) > 3 and len(title.split()) <= 15:  # Reasonable title length
                    return title
        
        return "Untitled Story"  # Default if no valid title found

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
        # Handle common abbreviations to avoid false splits
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

    def _process_text(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Process text with improved chunking and title extraction."""
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Extract title first
            title = self._extract_title(text)
            
            # Use Gemini to extract only story content
            prompt = f'''
            Extract and return ONLY the actual story narrative from this text.
            Exclude the title, table of contents, and any metadata.
            Return only the cleaned narrative text.

            Text to process:
            {text[:8000]}
            '''
            
            response = self.model.generate_content(prompt)
            story_text = response.text
            
            # Clean up the extracted text
            story_text = re.sub(r'^\d+\.\s+', '', story_text, flags=re.MULTILINE)
            story_text = re.sub(r'(?i)(^|\n)(Start|End)\s+of.*?\n', '\n', story_text)
            
            # Split into sentences and create chunks
            sentences = self._split_into_sentences(story_text)
            chunks = self._create_chunks(sentences)
            
            # Add title as first chunk if valid
            if title != "Untitled Story":
                chunks.insert(0, {
                    'text': f"Title: {title}",
                    'image_url': None,
                    'audio_url': None,
                    'is_title': True  # Mark as title chunk
                })
            
            logger.info(f"Processed text into {len(chunks)} chunks (including title)")
            return title, chunks[:self.max_paragraphs]
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise

    def _process_text(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Process text with improved chunking and title extraction."""
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Extract title first
            title = self._extract_title(text)
            
            # Use Gemini to extract only story content
            prompt = f'''
            Extract and return ONLY the actual story narrative from this text.
            Exclude the title, table of contents, and any metadata.
            Return only the cleaned narrative text.

            Text to process:
            {text[:8000]}
            '''
            
            response = self.model.generate_content(prompt)
            story_text = response.text
            
            # Clean up the extracted text
            story_text = re.sub(r'^\d+\.\s+', '', story_text, flags=re.MULTILINE)
            story_text = re.sub(r'(?i)(^|\n)(Start|End)\s+of.*?\n', '\n', story_text)
            
            # Split into sentences and create chunks
            sentences = self._split_into_sentences(story_text)
            chunks = self._create_chunks(sentences)
            
            # Add title as first chunk if valid
            if title != "Untitled Story":
                chunks.insert(0, {
                    'text': f"Title: {title}",
                    'image_url': None,
                    'audio_url': None,
                    'is_title': True  # Mark as title chunk
                })
            
            logger.info(f"Processed text into {len(chunks)} chunks (including title)")
            return title, chunks[:self.max_paragraphs]
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
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
            os.makedirs('uploads', exist_ok=True)
            file.save(temp_path)
            
            try:
                if ext == 'pdf':
                    title, paragraphs = self.process_pdf(temp_path)
                elif ext == 'epub':
                    title, paragraphs = self.process_epub(temp_path)
                else:  # html
                    title, paragraphs = self.process_html(temp_path)
                    
                # Store processed data in temporary storage
                temp_id = str(uuid.uuid4())
                temp_data = TempBookData(
                    id=temp_id,
                    data={
                        'source_file': filename,
                        'title': title,
                        'paragraphs': paragraphs
                    }
                )
                db.session.add(temp_data)
                db.session.commit()
                
                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'title': title,
                    'paragraphs': paragraphs
                }
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def process_pdf(self, file_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Extract and process text from PDF files."""
        try:
            raw_text = self._extract_pdf_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def process_epub(self, file_path: str) -> Tuple[str, List[Dict[str, str]]]:
        """Extract and process text from EPUB files."""
        try:
            raw_text = self._extract_epub_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing EPUB: {str(e)}")
            raise

    def process_html(self, file_path: str) -> Tuple[str, List[Dict[str, str]]]:
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
