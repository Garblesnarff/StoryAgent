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

    def _clean_paragraph(self, text: str) -> str:
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
        text = text.strip()
        
        return text if len(text) > 30 else ''  # Only return substantial paragraphs

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process extracted text into structured paragraphs with metadata."""
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            try:
                # Try Gemini first
                prompt = f'''
                Process this book text and extract the first chapter's content.
                Split it into natural paragraphs while preserving the story flow.
                Remove any metadata, page numbers, or markers.
                
                Text to process:
                {text[:4000]}  # Process first portion to get started
                '''
                
                response = self.model.generate_content(prompt)
                processed_text = response.text
                
            except Exception as api_error:
                print(f"Gemini API error: {str(api_error)}")
                # Fall back to basic text processing
                processed_text = text
            
            # Split into paragraphs using various common markers
            paragraphs = []
            for raw_paragraph in processed_text.split('\n\n'):
                clean_paragraph = self._clean_paragraph(raw_paragraph)
                if clean_paragraph:
                    paragraphs.append(clean_paragraph)
            
            # If no paragraphs found, try other delimiters
            if not paragraphs:
                for raw_paragraph in processed_text.split('.'):
                    if len(raw_paragraph.strip()) > 50:  # Only keep substantial paragraphs
                        clean_paragraph = self._clean_paragraph(raw_paragraph)
                        if clean_paragraph:
                            paragraphs.append(clean_paragraph)
            
            # Create paragraph entries
            processed_paragraphs = []
            for p in paragraphs[:10]:  # Limit to first 10 paragraphs
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

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text)
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()
