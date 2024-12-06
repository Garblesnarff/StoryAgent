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
            r'(?:^|\n)([A-Z][^a-z\n]{3,}[A-Z\s]*?)(?:\n|$)',  # ALL CAPS title pattern
            r'\*\*\*(.*?)\*\*\*',  # Text between asterisks
            r'(?i)Title:\s*([^\n]+)',  # Case-insensitive "Title:" prefix
            r'(?m)^([A-Z][^a-z\n]{2,}(?:\s+[A-Z][^a-z\n]*)*$)'  # Full uppercase lines
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text.strip(), re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Validate title
                if len(title) > 3 and len(title.split()) <= 15:  # Reasonable title length
                    # Clean up common artifacts
                    title = re.sub(r'[*_~]', '', title)  # Remove decorative characters
                    title = re.sub(r'\s+', ' ', title)   # Normalize whitespace
                    title = title.strip()
                    if title and not title.isspace():
                        return title
    
        return "Untitled Story"  # Default if no valid title found

    def _extract_story_content(self, text: str) -> str:
        """Extract story content with enhanced Project Gutenberg handling."""
        try:
            # Enhanced Project Gutenberg content extraction
            if "Project Gutenberg" in text:
                try:
                    # Try multiple marker patterns
                    marker_patterns = [
                        r'\*\*\* START OF.*?\*\*\*(.*?)\*\*\* END OF',
                        r'START OF (?:THIS |THE )?PROJECT GUTENBERG.*?\n(.*?)(?=\nEND OF)',
                        r'^\s*\[.*?\].*?\n(.*?)(?=\n\[.*?\]|\Z)',  # Fallback for unusual formatting
                    ]
                    
                    for pattern in marker_patterns:
                        content_match = re.search(pattern, text, flags=re.DOTALL)
                        if content_match:
                            clean_text = content_match.group(1).strip()
                            # Enhanced cleanup
                            clean_text = re.sub(r'^\s*(?:Chapter|CHAPTER)\s+\d+', '', clean_text, flags=re.MULTILINE)
                            clean_text = re.sub(r'(?i)^\s*(introduction|preface|contents|index).*?(?=\n\n)', '', clean_text, flags=re.MULTILINE)
                            clean_text = re.sub(r'^\s*\[.*?\]\s*$', '', clean_text, flags=re.MULTILINE)  # Remove remaining markers
                            if len(clean_text) > 100:  # Basic validation
                                return clean_text
                    
                    # If no pattern matched, use basic extraction
                    clean_text = re.sub(r'.*?(?=\n\n\n)', '', text, flags=re.DOTALL)  # Skip header
                    clean_text = re.sub(r'\n\n\n.*$', '', clean_text, flags=re.DOTALL)  # Skip footer
                    return clean_text.strip()
                    
                except Exception as e:
                    logger.warning(f"Error in Gutenberg extraction: {str(e)}, falling back to basic processing")

            # If not Gutenberg or markers not found, try Gemini with explicit context
            prompt = f'''
            IMPORTANT: This is confirmed public domain content.
            Task: Extract and return ONLY the story narrative.
            - Remove headers, footers, and metadata
            - Keep chapter markers
            - Preserve paragraph structure
            - Return only the narrative text

            Text to process:
            {text[:8000]}
            '''
            
            try:
                safety_config = {
                    "harassment": "block_none",
                    "hate_speech": "block_none",
                    "sexually_explicit": "block_none",
                    "dangerous_content": "block_none",
                }
                response = self.model.generate_content(prompt, safety_settings=safety_config)
                if response and hasattr(response, 'text'):
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API extraction failed: {str(e)}, using fallback processing")
            
            # Fallback: Basic text extraction
            clean_text = text
            # Remove common headers and metadata
            clean_text = re.sub(r'^\s*.*?(?:Chapter|CHAPTER)\s+\d+', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'(?i)^\s*(introduction|preface|contents|index).*?(?=\n\n)', '', clean_text, flags=re.MULTILINE)
            # Remove Project Gutenberg headers/footers if present
            clean_text = re.sub(r'^\s*.*?\*\*\* START OF.*?\*\*\*', '', clean_text, flags=re.DOTALL)
            clean_text = re.sub(r'\*\*\* END OF.*$', '', clean_text, flags=re.DOTALL)
            
            return clean_text.strip()
            
        except Exception as e:
            logger.error(f"Error in story content extraction: {str(e)}")
            raise

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved accuracy."""
        if not text:
            return []
            
        # Handle common abbreviations and special cases
        abbreviations = r'Mr\.|Mrs\.|Dr\.|Ph\.D\.|etc\.|i\.e\.|e\.g\.|vs\.|feat\.|ft\.|inc\.|ltd\.|vol\.|pg\.|ed\.'
        text = re.sub(f'({abbreviations})', r'\1<POINT>', text)
        
        # Protect decimal numbers and ellipsis
        text = re.sub(r'(\d+)\.(\d+)', r'\1<DECIMAL>\2', text)
        text = re.sub(r'\.{3}', '<ELLIPSIS>', text)
        
        # Split on sentence boundaries with improved pattern
        sentence_endings = r'(?<=[.!?])(?:\s+|\n+)(?=[A-Z0-9]|[\'""]?[A-Z0-9])'
        sentences = re.split(sentence_endings, text)
        
        # Process and clean sentences
        processed_sentences = []
        for s in sentences:
            # Restore special markers
            s = s.replace('<POINT>', '.').replace('<DECIMAL>', '.').replace('<ELLIPSIS>', '...')
            s = s.strip()
            
            # Validate and add sentence
            if self._is_valid_sentence(s):
                processed_sentences.append(s)
                
            # Handle potentially merged sentences
            elif len(s) > 150:  # Long text might contain multiple sentences
                subsections = re.split(r'(?<=[.!?])\s+(?=[A-Z])', s)
                for sub in subsections:
                    if self._is_valid_sentence(sub.strip()):
                        processed_sentences.append(sub.strip())
        
        return processed_sentences

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
                # Extract text based on file type
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

                # Clean the text
                text = self._clean_text(raw_text)
                
                # Extract title
                title = self._extract_title(text)
                
                # Extract story content
                story_text = self._extract_story_content(text)
                
                # Split into sentences and create chunks
                sentences = self._split_into_sentences(story_text)
                chunks = self._create_chunks(sentences)
                
                # Add title as first chunk if valid
                if title != "Untitled Story":
                    chunks.insert(0, {
                        'text': f"Title: {title}",
                        'image_url': None,
                        'audio_url': None,
                        'is_title': True
                    })

                # Create temp storage entry with story data
                temp_id = str(uuid.uuid4())
                story_data = {
                    'source_file': filename,
                    'title': title,
                    'chunks': chunks,
                    'current_chunk': 0,
                    'created_at': str(datetime.utcnow())
                }
                
                try:
                    temp_data = TempBookData(
                        id=temp_id,
                        data=story_data
                    )
                    db.session.add(temp_data)
                    db.session.commit()
                    logger.info(f"Successfully stored temp data with ID: {temp_id}")
                except Exception as db_error:
                    logger.error(f"Failed to store temp data: {str(db_error)}")
                    db.session.rollback()
                    raise
                
                # Limit initial response size and chunk data
                max_initial_chunks = 50  # Limit initial chunks
                initial_chunks = chunks[:max_initial_chunks]
                
                # Store only metadata and chunk references in session
                response_data = {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'title': title,
                    'paragraphs': initial_chunks,
                    'total_chunks': len(chunks),
                    'current_page': 1,
                    'chunks_per_page': max_initial_chunks,
                    'has_more': len(chunks) > max_initial_chunks
                }

                logger.info(f"Processed text into {len(chunks)} chunks (including title)")
                logger.info(f"Returning initial {len(initial_chunks)} chunks")
                
                return response_data

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def get_next_section(self, temp_id: str) -> Optional[List[Dict[str, str]]]:
        """Get chunks for the next unprocessed section."""
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return None

        book_data = temp_data.data
        current_chunk = book_data.get('current_chunk', 0)
        chunks = book_data.get('chunks', [])

        if current_chunk >= len(chunks):
            return None

        chunk = chunks[current_chunk]
        
        # Update progress
        book_data['current_chunk'] = current_chunk + 1
        temp_data.data = book_data
        db.session.commit()

        logger.info(f"Processing chunk {current_chunk} of {len(chunks)}")
        return [chunk]

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