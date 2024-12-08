import os
import logging
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import Optional, Dict, Callable

logger = logging.getLogger(__name__)

class TextExtractor:
    """Handles extraction of text content from different file formats."""
    
    def __init__(self):
        """Initialize TextExtractor with supported formats."""
        self.extractors: Dict[str, Callable[[str], str]] = {
            'pdf': self.extract_from_pdf,
            'epub': self.extract_from_epub,
            'html': self.extract_from_html,
            'txt': self.extract_from_txt
        }
    
    def extract_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file with enhanced error handling and metadata preservation.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file is corrupted or unreadable
        """
        text = []
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                # Extract metadata if available
                metadata = reader.metadata
                if metadata:
                    text.append(f"Title: {metadata.get('/Title', 'Unknown')}")
                    text.append(f"Author: {metadata.get('/Author', 'Unknown')}")
                    text.append("\n")
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text.append(f"[Page {page_num}]\n{page_text}")
                    
            return "\n".join(text)
        except Exception as e:
            logger.error(f"PDF extraction failed for {pdf_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_from_epub(self, epub_path: str) -> str:
        """
        Extract text from EPUB file with chapter preservation.
        
        Args:
            epub_path (str): Path to the EPUB file
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file is corrupted or unreadable
        """
        text = []
        try:
            book = epub.read_epub(epub_path)
            
            # Extract metadata
            if book.get_metadata('DC', 'title'):
                text.append(f"Title: {book.get_metadata('DC', 'title')[0][0]}")
            if book.get_metadata('DC', 'creator'):
                text.append(f"Author: {book.get_metadata('DC', 'creator')[0][0]}")
            text.append("\n")
            
            # Extract content
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract chapter titles
                    chapter_title = soup.find(['h1', 'h2'])
                    if chapter_title:
                        text.append(f"\n[Chapter: {chapter_title.get_text().strip()}]\n")
                        
                    if soup.get_text():
                        text.append(soup.get_text().strip())
                        
            return "\n".join(text)
        except Exception as e:
            logger.error(f"EPUB extraction failed for {epub_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from EPUB: {str(e)}")
    
    def extract_from_html(self, html_path: str) -> str:
        """
        Extract text from HTML file with content structure preservation.
        
        Args:
            html_path (str): Path to the HTML file
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file is corrupted or unreadable
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                
                # Remove unwanted elements
                for tag in soup(['script', 'style', 'meta', 'link', 'nav', 'footer']):
                    tag.decompose()
                
                # Extract title
                title = soup.title.string if soup.title else "Untitled"
                content = [f"Title: {title}\n"]
                
                # Extract headings and content
                for element in soup.find_all(['h1', 'h2', 'h3', 'p']):
                    if element.name.startswith('h'):
                        content.append(f"\n[{element.get_text().strip()}]\n")
                    else:
                        content.append(element.get_text().strip())
                        
                return "\n".join(content)
        except Exception as e:
            logger.error(f"HTML extraction failed for {html_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from HTML: {str(e)}")
    
    def extract_from_txt(self, txt_path: str) -> str:
        """
        Extract text from plain text file with basic formatting preservation.
        
        Args:
            txt_path (str): Path to the text file
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file is corrupted or unreadable
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Normalize line endings
                content = content.replace('\r\n', '\n').replace('\r', '\n')
                return content
        except Exception as e:
            logger.error(f"TXT extraction failed for {txt_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from TXT: {str(e)}")

    def extract_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text based on file type with enhanced error handling.
        
        Args:
            file_path (str): Path to the input file
            file_type (str): Type of the file (pdf, epub, html, txt)
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file type is unsupported or extraction fails
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
            
        file_type = file_type.lower()
        if file_type not in self.extractors:
            raise ValueError(f"Unsupported file type: {file_type}")
            
        try:
            logger.info(f"Extracting text from {file_type} file: {file_path}")
            return self.extractors[file_type](file_path)
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            raise ValueError(f"Text extraction failed: {str(e)}")
