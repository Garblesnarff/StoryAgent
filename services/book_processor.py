from typing import List, Dict
import PyPDF2
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import google.generativeai as genai
import nltk
from nltk.tokenize import sent_tokenize

class BookProcessor:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        
        # Download NLTK data for sentence tokenization
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
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
        
        # Clean up special characters
        text = text.replace('_', '')
        text = re.sub(r'={3,}', '', text)  # Remove section separators
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('--', '—')
        text = re.sub(r'\s*\[\d+\]\s*', '', text)  # Remove reference numbers
        
        # Fix common OCR issues
        text = re.sub(r'(\w)- (\w)', r'\1\2', text)  # Fix hyphenated words
        
        return text.strip()

    def _is_valid_sentence(self, sentence: str) -> bool:
        """Check if a sentence is valid and meaningful."""
        # Remove whitespace and check minimum length
        cleaned = sentence.strip()
        if len(cleaned) < 20:  # Minimum meaningful sentence length
            return False
            
        # Check if it contains actual words (not just numbers or symbols)
        if not re.search(r'[a-zA-Z]{2,}', cleaned):
            return False
            
        # Check for balanced quotes and parentheses
        quotes = cleaned.count('"') + cleaned.count('"') + cleaned.count('"')
        if quotes % 2 != 0:
            return False
            
        parens = cleaned.count('(') - cleaned.count(')')
        if parens != 0:
            return False
            
        return True

    def _process_text(self, text: str) -> List[Dict[str, str]]:
        """Process extracted text into two-sentence chunks."""
        try:
            # Clean the text first
            text = self._clean_text(text)
            
            # Use NLTK to split into sentences with proper boundary detection
            sentences = sent_tokenize(text)
            
            # Filter valid sentences
            valid_sentences = [s.strip() for s in sentences if self._is_valid_sentence(s)]
            
            # Create chunks of two sentences
            chunks = []
            for i in range(0, len(valid_sentences)-1, 2):
                # Get the next two sentences
                first_sentence = valid_sentences[i].strip()
                second_sentence = valid_sentences[i+1].strip()
                
                # Only create chunk if both sentences are valid
                if first_sentence and second_sentence:
                    # Join sentences with proper spacing
                    chunk_text = f"{first_sentence} {second_sentence}"
                    
                    # Create the paragraph object
                    chunks.append({
                        'text': chunk_text,
                        'image_url': None,
                        'audio_url': None
                    })
            
            # Handle the last sentence if there's an odd number
            if len(valid_sentences) % 2 != 0 and valid_sentences[-1]:
                last_sentence = valid_sentences[-1].strip()
                if len(chunks) > 0:
                    # Append to the last chunk if possible
                    chunks[-1]['text'] += f" {last_sentence}"
                else:
                    # Create a new chunk if it's the only sentence
                    chunks.append({
                        'text': last_sentence,
                        'image_url': None,
                        'audio_url': None
                    })
            
            return chunks
            
        except Exception as e:
            print(f"Error processing text: {str(e)}")
            return []

    def _clean_paragraph(self, text: str) -> str:
        """Clean individual paragraph text."""
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
        
        return text.strip() if len(text) > 30 else ''  # Only return substantial paragraphs
