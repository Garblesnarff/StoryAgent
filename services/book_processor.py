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
        self.model = genai.GenerativeModel('gemini-1.0-pro')
        
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
        """Process extracted text into structured chapters with metadata."""
        try:
            # Clean the text
            text = self._clean_text(text)
            
            # Split into chapters using common chapter markers
            chapter_pattern = r'(?i)(?:chapter|book|part)\s+(?:[IVX]+|\d+|\w+)(?:\s*[-:]\s*\w+)?'
            chapters = re.split(chapter_pattern, text)
            
            # Remove empty chapters and limit to first 10
            chapters = [ch.strip() for ch in chapters if ch.strip()][:10]
            
            processed_chapters = []
            for chapter in chapters:
                # Use Gemini to analyze the chapter
                prompt = f"""
                Analyze this chapter text and provide:
                1. A cleaned, well-formatted version of the text
                2. A brief description for image generation
                3. The emotional tone for audio narration

                Text:
                {chapter[:1000]}  # Process first 1000 chars to stay within limits
                """
                
                response = self.model.generate_content(prompt)
                if response.text:
                    parts = response.text.split('\n\n')
                    processed = {
                        'text': parts[0] if len(parts) > 0 else chapter,
                        'scene_description': parts[1] if len(parts) > 1 else '',
                        'emotional_tone': parts[2] if len(parts) > 2 else 'neutral',
                        'image_url': None,
                        'audio_url': None
                    }
                    processed_chapters.append(processed)
                    
            return processed_chapters
            
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return []
