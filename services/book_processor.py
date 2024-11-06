from typing import List, Dict
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re

class BookProcessor:
    def __init__(self):
        pass
        
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
        try:
            # Clean the text
            text = self._clean_text(text)
            
            # Find chapters using regex
            chapter_pattern = r'(?i)(?:chapter|book|part)\s+(?:[IVX]+|\d+|\w+)(?:\s*[-:]\s*[\w\s]+)?'
            chapter_matches = list(re.finditer(chapter_pattern, text))
            
            if not chapter_matches:
                # If no chapters found, treat entire text as one chapter
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                return [{'text': p, 'image_url': None, 'audio_url': None} for p in paragraphs[:10]]
            
            # Get first chapter's content
            chapter_start = chapter_matches[0].start()
            next_chapter_start = chapter_matches[1].start() if len(chapter_matches) > 1 else len(text)
            first_chapter = text[chapter_start:next_chapter_start].strip()
            
            # Remove chapter heading
            first_chapter = re.sub(chapter_pattern, '', first_chapter, count=1).strip()
            
            # Split first chapter into paragraphs
            paragraphs = [p.strip() for p in first_chapter.split('\n\n') if p.strip()]
            
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
