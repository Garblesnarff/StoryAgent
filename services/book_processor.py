from typing import List, Dict
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
from services.text_generator import TextGenerator
from services.image_generator import ImageGenerator
from services.hume_audio_generator import HumeAudioGenerator

class BookProcessor:
    def __init__(self):
        self.text_generator = TextGenerator()
        self.image_generator = ImageGenerator()
        self.audio_generator = HumeAudioGenerator()
        
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
        # Split into paragraphs and clean each
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        # Join cleaned paragraphs
        return '\n\n'.join(paragraphs)

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process extracted text into structured paragraphs with media."""
        try:
            # Clean the text
            text = self._clean_text(text)
            
            # Split into paragraphs and process a maximum of 10
            paragraphs = [p for p in text.split('\n\n') if p.strip()][:10]
            
            processed_paragraphs = []
            for paragraph in paragraphs:
                # Clean each paragraph individually
                cleaned_text = self.text_generator.clean_paragraph(paragraph)
                if cleaned_text:
                    # Generate media for the paragraph
                    processed = {
                        'text': cleaned_text,
                        'image_url': self.image_generator.generate_image(cleaned_text),
                        'audio_url': self.audio_generator.generate_audio(cleaned_text)
                    }
                    processed_paragraphs.append(processed)
                    
            return processed_paragraphs

        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return []
