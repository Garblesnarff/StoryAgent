import os
import logging
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import Optional

logger = logging.getLogger(__name__)

class TextExtractor:
    """Handles extraction of text content from different file formats."""
    
    @staticmethod
    def extract_from_pdf(pdf_path: str) -> str:
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
            logger.error(f"PDF extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def extract_from_epub(epub_path: str) -> str:
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
            logger.error(f"EPUB extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def extract_from_html(html_path: str) -> str:
        """Extract text from HTML file."""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                for tag in soup(['script', 'style', 'meta', 'link']):
                    tag.decompose()
                return soup.get_text()
        except Exception as e:
            logger.error(f"HTML extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def extract_from_txt(txt_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"TXT extraction failed: {str(e)}")
            raise

    def extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """Extract text based on file type."""
        extractors = {
            'pdf': self.extract_from_pdf,
            'epub': self.extract_from_epub,
            'html': self.extract_from_html,
            'txt': self.extract_from_txt
        }
        
        if file_type not in extractors:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        return extractors[file_type](file_path)
