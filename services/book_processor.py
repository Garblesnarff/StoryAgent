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

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        try:
            # Clean the text initially
            text = self._clean_text(text)
            
            # Use Gemini to identify chapter boundaries and split text
            prompt = f'''
            Find and extract chapters from this text. For each chapter:
            1. Keep the exact original text
            2. Preserve all original punctuation and formatting
            3. Do not summarize or rewrite the content
            4. Split into original paragraphs
            5. Remove only chapter markers and page numbers
            
            Return the raw text exactly as it appears in the book, split into its natural paragraphs.
            
            Text to process:
            {text[:8000]}
            '''
            
            response = self.model.generate_content(prompt)
            processed_text = response.text
            
            # Split into paragraphs and clean each one
            paragraphs = []
            
            # First try splitting by double newlines (standard paragraph breaks)
            raw_paragraphs = processed_text.split('\n\n')
            
            for raw_paragraph in raw_paragraphs:
                if raw_paragraph.strip():
                    clean_paragraph = self._clean_paragraph(raw_paragraph)
                    if clean_paragraph and len(clean_paragraph) > 30:  # Only keep substantial paragraphs
                        paragraphs.append({
                            'text': clean_paragraph,
                            'image_url': None,
                            'audio_url': None
                        })
            
            # If no paragraphs found, try basic text splitting
            if not paragraphs:
                # Split by single newlines and look for paragraph-like chunks
                text_chunks = text.split('\n')
                current_paragraph = []
                
                for chunk in text_chunks:
                    chunk = chunk.strip()
                    if chunk:
                        current_paragraph.append(chunk)
                    elif current_paragraph:
                        # Join accumulated lines and clean
                        paragraph_text = ' '.join(current_paragraph)
                        clean_paragraph = self._clean_paragraph(paragraph_text)
                        if clean_paragraph and len(clean_paragraph) > 30:
                            paragraphs.append({
                                'text': clean_paragraph,
                                'image_url': None,
                                'audio_url': None
                            })
                        current_paragraph = []
                
                # Handle any remaining paragraph
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    clean_paragraph = self._clean_paragraph(paragraph_text)
                    if clean_paragraph and len(clean_paragraph) > 30:
                        paragraphs.append({
                            'text': clean_paragraph,
                            'image_url': None,
                            'audio_url': None
                        })
            
            return paragraphs
                
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return []

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers
        text = re.sub(r'\b\d+\b(?=\s*$)', '', text)
        # Remove headers and footers (common in PDFs)
        text = re.sub(r'^\s*(?:chapter|page)\s+\d+\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        return text.strip()

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
