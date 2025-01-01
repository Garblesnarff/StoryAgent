import logging
from typing import List, Dict, Tuple
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
import re
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
        self.upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        self.chunks_per_batch = 10  # Keep the same batch size that was working

        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model = None

        try:
            if not self.api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")
                return

            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Successfully initialized Gemini API")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")

    def process_file(self, file) -> Dict[str, any]:
        """Process uploaded file and extract story chunks."""
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
            temp_path = os.path.join(self.upload_folder, filename)
            file.save(temp_path)

            try:
                if ext == 'pdf':
                    paragraphs = self.process_pdf(temp_path)
                elif ext == 'epub':
                    paragraphs = self.process_epub(temp_path)
                else:  # html
                    paragraphs = self.process_html(temp_path)

                if not paragraphs:
                    logger.warning(f"No valid paragraphs extracted from {filename}")
                    return {'error': 'No valid content found in file'}

                # Store only initial batch of paragraphs
                initial_batch = paragraphs[:self.chunks_per_batch]
                all_chunks_count = len(paragraphs)

                # Store processed data with metadata
                temp_id = str(uuid.uuid4())
                temp_data = TempBookData(
                    id=temp_id,
                    data={
                        'source_file': filename,
                        'paragraphs': initial_batch,
                        'total_chunks': all_chunks_count,
                        'current_position': self.chunks_per_batch
                    }
                )

                db.session.add(temp_data)
                db.session.commit()
                logger.info(f"Saved initial batch of processed book data with ID: {temp_id}")

                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'paragraphs': initial_batch,
                    'total_chunks': all_chunks_count,
                    'current_position': self.chunks_per_batch
                }

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return {'error': str(e)}

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process text into story chunks."""
        try:
            if not text:
                logger.error("No text provided for processing")
                return []

            # Clean the text initially
            text = self._clean_text(text)
            logger.info(f"Initial text length: {len(text)} characters")

            # Detect chapter boundaries
            start_idx, end_idx = self._detect_chapter_boundaries(text)
            first_chapter = text[start_idx:end_idx]
            logger.info(f"Extracted first chapter: {len(first_chapter)} characters")

            # Split into sentences
            sentences = self._split_into_sentences(first_chapter)
            logger.info(f"Extracted {len(sentences)} total sentences")

            # Group into 2-sentence chunks for the entire chapter
            story_chunks = []
            chunk_size = 2  # Keep the exact same 2-sentence chunk format that was working

            for i in range(0, len(sentences), chunk_size):
                chunk_sentences = sentences[i:i + chunk_size]
                if chunk_sentences:  # Ensure we have sentences
                    chunk_text = ' '.join(chunk_sentences)
                    if chunk_text and len(chunk_text.split()) >= 5:  # Basic validation
                        story_chunks.append({
                            'text': chunk_text,
                            'image_url': None,
                            'audio_url': None
                        })

            logger.info(f"Successfully processed {len(story_chunks)} two-sentence chunks from first chapter")
            return story_chunks

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return []

    def _detect_chapter_boundaries(self, text: str) -> Tuple[int, int]:
        """
        Detect the start and end indices of the first chapter in the text.
        Returns tuple of (start_index, end_index)
        """
        text_length = len(text)

        try:
            if not text:
                logger.error("Empty text provided")
                return 0, 0

            # Get a large enough sample to detect chapter boundaries
            sample_size = min(text_length, 50000)  # Increased sample size for better detection
            text_sample = text[:sample_size]

            # Try to identify chapter boundaries without API if possible
            chapter_start = 0
            chapter_end = text_length

            # Look for common chapter indicators
            chapter_patterns = [
                r'Chapter [0-9]+',
                r'CHAPTER [0-9]+',
                r'Chapter One',
                r'CHAPTER ONE'
            ]

            for pattern in chapter_patterns:
                match = re.search(pattern, text_sample)
                if match:
                    chapter_start = match.start()
                    break

            if chapter_start == 0:
                # If no chapter markers found, try to find the start of narrative content
                content_markers = [
                    r'\n\n[A-Z][^.!?]+[.!?]',  # Look for paragraph starting with capital letter
                    r'\n\s*[A-Z][^.!?]+[.!?]'  # Alternative paragraph format
                ]
                for marker in content_markers:
                    match = re.search(marker, text_sample)
                    if match:
                        chapter_start = match.start()
                        break

            # Try to find the end of the first chapter
            next_chapter_patterns = [
                r'\nChapter [0-9]+',
                r'\nCHAPTER [0-9]+',
                r'\nChapter Two',
                r'\nCHAPTER TWO'
            ]

            for pattern in next_chapter_patterns:
                match = re.search(pattern, text[chapter_start:])
                if match:
                    chapter_end = chapter_start + match.start()
                    break

            logger.info(f"Detected chapter boundaries: {chapter_start} to {chapter_end}")
            return chapter_start, chapter_end

        except Exception as e:
            logger.error(f"Error detecting chapter boundaries: {str(e)}")
            return 0, text_length

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Basic text cleaning
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved handling of edge cases."""
        if not text:
            return []

        # Clean text first
        text = self._clean_text(text)

        # Split into sentences
        sentences = []
        # Split on sentence endings followed by capital letters
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

        for raw_sentence in raw_sentences:
            # Clean and validate each sentence
            cleaned = raw_sentence.strip()
            if cleaned and len(cleaned.split()) > 3:  # Ensure minimum word count
                if not cleaned[-1] in '.!?':  # Add period if missing sentence ending
                    cleaned += '.'
                sentences.append(cleaned)

        return sentences

    def process_pdf(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from PDF files."""
        try:
            raw_text = self._extract_pdf_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return []

    def process_epub(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from EPUB files."""
        try:
            raw_text = self._extract_epub_text(file_path)
            return self._process_text(raw_text)
        except Exception as e:
            logger.error(f"Error processing EPUB: {str(e)}")
            return []

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
            return []

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
            return ""

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
            return ""