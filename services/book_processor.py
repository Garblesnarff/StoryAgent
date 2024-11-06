from typing import List, Dict
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import google.generativeai as genai

class BookProcessor:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    def process_pdf(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from PDF files."""
        raw_text = self._extract_pdf_text(file_path)
        return self._process_text(raw_text)
    
    def process_epub(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from EPUB files."""
        raw_text = self._extract_epub_text(file_path)
        return self._process_text(raw_text)
    
    def process_html(self, file_path: str) -> List[Dict[str, str]]:
        """Extract and process text from HTML files."""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            # Remove scripts, styles, and other non-content elements
            for tag in soup(['script', 'style', 'meta', 'link']):
                tag.decompose()
            raw_text = soup.get_text()
            return self._process_text(raw_text)

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text

    def _extract_epub_text(self, epub_path: str) -> str:
        """Extract text from EPUB file."""
        book = epub.read_epub(epub_path)
        text = ""
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
        return text

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text)
        # Remove headers and footers (common in PDFs)
        text = re.sub(r'^\s*(?:chapter|page)\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # Clean up quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process extracted text into structured paragraphs with metadata."""
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Use Gemini to process and clean the text
            prompt = f'''
            Process this book text and extract the first chapter's content.
            1. Identify and extract the complete first chapter
            2. Split it into natural paragraphs
            3. Remove any metadata, page numbers, or markers
            4. Preserve all the original story text and paragraph breaks
            5. Return the complete chapter text split into paragraphs
            
            Text to process:
            {text}
            '''
            
            # Get clean text from Gemini
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return []
                
            # Split into paragraphs
            paragraphs = [p.strip() for p in response.text.split('\n\n') if p.strip()]
            
            # Create paragraph entries for all paragraphs
            processed_paragraphs = []
            for p in paragraphs:
                if p:
                    processed = {
                        'text': p,
                        'image_url': None,
                        'audio_url': None
                    }
                    processed_paragraphs.append(processed)
            
            return processed_paragraphs
                
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return []
