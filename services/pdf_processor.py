from google.generativeai import GenerativeModel
import base64
import PyPDF2
import os
import logging
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.model = GenerativeModel('gemini-1.5-flash')
        
    def extract_text_from_pdf(self, pdf_file):
        """Extract raw text from PDF file"""
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def extract_text_from_epub(self, epub_path):
        """Extract text from EPUB file"""
        try:
            book = epub.read_epub(epub_path)
            text = ""
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from EPUB: {str(e)}")
            raise

    def extract_text_from_html(self, html_file):
        """Extract text from HTML file"""
        try:
            soup = BeautifulSoup(html_file.read(), 'html.parser')
            return soup.get_text()
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            raise

    def clean_text(self, text):
        """Clean and normalize extracted text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers
        text = re.sub(r'\n\d+\n', '\n', text)
        # Fix common OCR issues
        text = text.replace('¬', '')
        text = text.replace('|', 'I')
        return text.strip()

    async def analyze_text_structure(self, text):
        """Use Gemini to analyze text and split into proper paragraphs"""
        try:
            prompt = f'''Analyze this text and split it into proper paragraphs. 
            Ensure each paragraph is a complete thought or scene.
            Remove any headers, footers, or page numbers.
            Text to analyze: 
            {text[:4000]}'''
            
            response = await self.model.generate_content(prompt)
            result = response.text if hasattr(response, 'text') else response.parts[0].text
            return self._parse_paragraphs(result)
        except Exception as e:
            logger.error(f"Error analyzing text structure: {str(e)}")
            raise

    def _parse_paragraphs(self, text):
        """Parse Gemini's response into clean paragraphs"""
        # Split on double newlines
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        # Remove any remaining artifacts
        paragraphs = [re.sub(r'^[0-9]+[\.\)]\s*', '', p) for p in paragraphs]
        return paragraphs

    async def process_document(self, file, file_type):
        """Process document file end-to-end"""
        temp_path = None
        try:
            # Save file temporarily
            temp_path = os.path.join('uploads', f'temp_{int(time.time())}.{file_type}')
            with open(temp_path, 'wb') as f:
                f.write(file.read())
            
            # Extract text based on file type
            if file_type == 'pdf':
                with open(temp_path, 'rb') as f:
                    raw_text = self.extract_text_from_pdf(f)
            elif file_type == 'epub':
                raw_text = self.extract_text_from_epub(temp_path)
            elif file_type == 'html':
                with open(temp_path, 'r', encoding='utf-8') as f:
                    raw_text = self.extract_text_from_html(f)
                    
            # Clean up temp file
            os.remove(temp_path)
            temp_path = None
            
            # Continue with existing processing
            cleaned_text = self.clean_text(raw_text)
            text_chunks = [cleaned_text[i:i+4000] for i in range(0, len(cleaned_text), 4000)]
            
            all_paragraphs = []
            for chunk in text_chunks:
                chunk_paragraphs = await self.analyze_text_structure(chunk)
                all_paragraphs.extend(chunk_paragraphs)
            
            return all_paragraphs
                
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Error processing document: {str(e)}")
            raise
