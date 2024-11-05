from google.generativeai import GenerativeModel
import base64
import PyPDF2
import os
import logging
import re

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
            prompt = f"""Analyze this text and split it into proper paragraphs. 
            Ensure each paragraph is a complete thought or scene.
            Remove any headers, footers, or page numbers.
            Text to analyze: 
            {text[:4000]}"""  # Limit text chunk size
            
            response = await self.model.generate_content(prompt)
            return self._parse_paragraphs(response.text)
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

    async def process_pdf(self, pdf_file):
        """Process PDF file end-to-end"""
        try:
            # Extract raw text
            raw_text = self.extract_text_from_pdf(pdf_file)
            logger.info(f"Extracted {len(raw_text)} characters from PDF")
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            logger.info("Text cleaned and normalized")
            
            # Split into chunks if text is very long
            text_chunks = [cleaned_text[i:i+4000] for i in range(0, len(cleaned_text), 4000)]
            logger.info(f"Split text into {len(text_chunks)} chunks")
            
            # Process each chunk
            all_paragraphs = []
            for chunk in text_chunks:
                chunk_paragraphs = await self.analyze_text_structure(chunk)
                all_paragraphs.extend(chunk_paragraphs)
            
            logger.info(f"Generated {len(all_paragraphs)} paragraphs")
            return all_paragraphs
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
