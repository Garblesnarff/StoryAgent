from typing import List, Dict, Tuple
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
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.model = None

        try:
            if not self.api_key:
                logger.warning("GEMINI_API_KEY not found in environment variables")
                return

            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
            logger.info("Successfully initialized Gemini API")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")

    def _validate_api_setup(self) -> bool:
        """Check if the API is properly configured."""
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return False
        if not self.model:
            logger.error("Gemini model not initialized")
            return False
        return True

    def _detect_chapter_boundaries(self, text: str) -> Tuple[int, int]:
        """
        Detect the start and end indices of the first chapter in the text.
        Returns tuple of (start_index, end_index)
        """
        try:
            if not self._validate_api_setup():
                text_length = len(text)
                return 0, min(text_length, 12000)  # Default to first 12000 chars if API not available

            # Use multiple chunks to better identify chapter boundaries
            text_length = len(text)
            chunk_size = 12000  # Increased chunk size
            chunks_to_analyze = min(3, (text_length + chunk_size - 1) // chunk_size)

            full_text_to_analyze = text[:chunks_to_analyze * chunk_size]

            # Use Gemini to identify chapter boundaries
            prompt = f'''
            Analyze this text and identify ONLY the exact start and end of the first chapter.
            Return your response in this exact format:
            START_INDEX: [number]
            END_INDEX: [number]

            Rules:
            1. Include chapter heading/title in the start
            2. Stop at the start of Chapter 2 or clear chapter break
            3. Include all paragraphs in Chapter 1
            4. Exclude table of contents or front matter
            5. If unsure of exact end, include more text rather than less

            Text to analyze:
            {full_text_to_analyze}
            '''

            response = self.model.generate_content(prompt)
            response_text = response.text

            # Extract indices from response
            start_match = re.search(r'START_INDEX:\s*(\d+)', response_text)
            end_match = re.search(r'END_INDEX:\s*(\d+)', response_text)

            if start_match and end_match:
                start_idx = int(start_match.group(1))
                end_idx = min(int(end_match.group(1)), text_length)

                # Validate the detected boundaries
                if start_idx < 0 or start_idx >= text_length or end_idx <= start_idx:
                    logger.warning("Invalid chapter boundaries detected, using default approach")
                    return 0, text_length

                logger.info(f"Detected chapter boundaries: {start_idx} to {end_idx}")
                return start_idx, end_idx

            logger.warning("Could not detect exact chapter boundaries, using default approach")
            return 0, text_length

        except Exception as e:
            logger.error(f"Error detecting chapter boundaries: {str(e)}")
            text_length = len(text) if text else 0  # Ensure text_length is defined
            return 0, text_length

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""

        # Remove common metadata sections and formatting
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        return text.strip()

    def _is_story_content(self, text: str) -> bool:
        """Check if text is story content rather than metadata or other non-story text."""
        try:
            # Refined content detection
            if not text or len(text.split()) < 10:  # Skip very short segments
                return False

            # Ensure text has proper sentence structure
            if not re.search(r'[A-Z][^.!?]+[.!?]', text):
                return False

            # Skip obvious metadata patterns
            metadata_patterns = [
                r'^\s*copyright\s+\d{4}',
                r'^\s*chapter\s+\d+\s*$',
                r'^\s*page\s+\d+\s*$',
                r'^\s*contents\s*$',
                r'^\s*acknowledgments\s*$'
            ]

            for pattern in metadata_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False

            return True
        except Exception:
            return False

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with improved handling of edge cases."""
        try:
            if not text:
                return []

            # First clean the text
            text = self._clean_text(text)

            # Split into potential sentences using multiple delimiters
            sentences = []
            # Split on sentence endings followed by capital letters
            raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

            for raw_sentence in raw_sentences:
                # Further clean and validate each sentence
                cleaned = raw_sentence.strip()
                if cleaned and len(cleaned.split()) > 3:  # Ensure minimum word count
                    if not cleaned[-1] in '.!?':  # Add period if missing sentence ending
                        cleaned += '.'
                    sentences.append(cleaned)

            return sentences
        except Exception as e:
            logger.error(f"Error splitting sentences: {str(e)}")
            return []

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process text into story chunks."""
        try:
            if not self._validate_api_setup():
                logger.error("Cannot process text: API not properly configured")
                return []

            # Clean the text initially
            text = self._clean_text(text)
            logger.info(f"Initial text length: {len(text)} characters")

            # Detect chapter boundaries
            start_idx, end_idx = self._detect_chapter_boundaries(text)
            first_chapter = text[start_idx:end_idx]
            logger.info(f"Extracted first chapter: {len(first_chapter)} characters")

            # Process chapter in chunks
            chunk_size = min(12000, len(first_chapter))  # Adjust chunk size based on chapter length
            chapter_chunks = [first_chapter[i:i + chunk_size]
                            for i in range(0, len(first_chapter), chunk_size)]

            processed_text = []
            for i, chunk in enumerate(chapter_chunks):
                try:
                    logger.info(f"Processing chunk {i+1}/{len(chapter_chunks)}")
                    prompt = f'''
                    Extract and clean the story narrative from this chapter text.
                    - Remove headers, page numbers, and metadata
                    - Preserve paragraph breaks
                    - Maintain sentence structure
                    - Return only the narrative text

                    Text to process:
                    {chunk}
                    '''

                    response = self.model.generate_content(prompt)
                    processed_text.append(response.text)
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1}: {str(chunk_error)}")
                    continue

            # Join processed text and split into sentences
            full_text = ' '.join(processed_text)
            sentences = self._split_into_sentences(full_text)
            logger.info(f"Extracted {len(sentences)} total sentences")

            # Group into 2-sentence chunks
            story_chunks = []
            for i in range(0, len(sentences), 2):
                try:
                    if i + 1 < len(sentences):
                        chunk_text = f"{sentences[i]} {sentences[i+1]}"
                    else:
                        chunk_text = sentences[i]

                    if self._is_story_content(chunk_text):
                        story_chunks.append({
                            'text': chunk_text,
                            'image_url': None,
                            'audio_url': None
                        })
                except Exception as chunk_error:
                    logger.error(f"Error creating chunk {i//2}: {str(chunk_error)}")
                    continue

            logger.info(f"Successfully processed {len(story_chunks)} two-sentence chunks from first chapter")
            return story_chunks

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return []

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
            temp_path = os.path.join('uploads', filename)
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

                # Store processed data
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
                logger.info(f"Saved processed book data with ID: {temp_id}")

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
            return {'error': str(e)}

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