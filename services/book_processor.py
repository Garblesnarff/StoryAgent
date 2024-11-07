from typing import List, Dict
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import google.generativeai as genai
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        
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
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            for page in reader.pages:
                text.append(page.extract_text())
            return "\n".join(text)

    def _extract_epub_text(self, epub_path: str) -> str:
        """Extract text from EPUB file."""
        book = epub.read_epub(epub_path)
        text = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text.append(soup.get_text())
        return "\n".join(text)

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process extracted text into structured paragraphs."""
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Process text in chunks to avoid token limits
            chunks = self._split_into_chunks(text, max_length=4000)
            paragraphs = []
            
            for chunk in chunks:
                # Use Gemini to process each chunk
                response = self.model.generate_content(
                    "Split this text into meaningful paragraphs while preserving the original content. "
                    "Remove any chapter markers, numbers, or formatting. Each paragraph should be a "
                    "complete thought or scene.\n\nText:\n" + chunk
                )
                
                # Process the response
                if response.text:
                    # Split into paragraphs and clean each one
                    chunk_paragraphs = [p.strip() for p in response.text.split('\n\n') if p.strip()]
                    for p in chunk_paragraphs:
                        clean_p = self._clean_paragraph(p)
                        if clean_p and len(clean_p) > 30:  # Only keep substantial paragraphs
                            paragraphs.append({
                                'text': clean_p,
                                'image_url': None,
                                'audio_url': None
                            })
            
            return paragraphs[:20]  # Limit to 20 paragraphs for performance
                
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text)
        # Remove headers and footers
        text = re.sub(r'^\s*(?:chapter|page)\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

    def _clean_paragraph(self, text: str) -> str:
        """Clean individual paragraphs."""
        if not text:
            return ''
            
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove page numbers
        text = re.sub(r'\d+(?=\s*$)', '', text)
        
        # Remove chapter markers
        text = re.sub(r'(?i)^chapter\s+\w+\s*:?\s*', '', text)
        
        # Remove any remaining segment markers
        text = re.sub(r'(?i)(?:segment|section|part|scene)\s*#?\d*:?\s*', '', text)
        
        # Clean up punctuation and spacing
        text = ' '.join(text.split())
        
        return text if len(text) > 30 else ''

    def _split_into_chunks(self, text: str, max_length: int = 4000) -> List[str]:
        """Split text into manageable chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > max_length:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
