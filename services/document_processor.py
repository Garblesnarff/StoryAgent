import google.generativeai as genai
import logging
import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Generator
import json
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile

class ProcessingStage(Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    PROCESSING = "processing" 
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ProcessingProgress:
    stage: ProcessingStage
    progress: float
    message: str
    details: Dict = None

class DocumentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        self.upload_dir = Path('uploads')
        self.upload_dir.mkdir(exist_ok=True)

    def _extract_epub_text(self, epub_path):
        book = epub.read_epub(epub_path)
        chapters = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                if text.strip():
                    chapters.append(text)
        return '\n\n'.join(chapters)

    def process_document(self, file_path: str) -> Generator[ProcessingProgress, None, None]:
        temp_path = None
        try:
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting document upload"
            )

            # Handle EPUB files by converting to text first
            file_extension = Path(file_path).suffix.lower()
            if file_extension == '.epub':
                text_content = self._extract_epub_text(file_path)
                # Create temporary text file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(text_content)
                    temp_path = temp_file.name
                file_path = temp_path

            # Upload file using Gemini's built-in file handling
            file_obj = genai.upload_file(file_path)
            
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=100,
                message="Document upload complete"
            )

            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document content"
            )

            prompt = '''Extract all text content from this document, properly formatted into paragraphs.
            Return only the clean text content, without any formatting markers, page numbers, or headers.
            Split into natural paragraphs based on content.'''

            response = self.model.generate_content(
                [prompt, file_obj]
            )

            if not response or not response.text:
                raise Exception("Failed to extract content from document")

            # Parse response into paragraphs
            paragraphs = [p.strip() for p in response.text.split('\n\n') if p.strip()]

            if not paragraphs:
                raise Exception("No valid text content extracted from document")

            story_data = {
                'paragraphs': [{
                    'text': p,
                    'image_url': None,
                    'audio_url': None
                } for p in paragraphs if len(p.strip()) > 0]
            }

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Processing complete",
                details=story_data
            )

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.error(f"Error cleaning up files: {str(e)}")
