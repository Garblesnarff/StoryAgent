import google.generativeai as genai
import logging
import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Generator
import json

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
        # Use gemini-1.5-flash-8b for better document processing
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        self.upload_dir = Path('uploads')
        self.upload_dir.mkdir(exist_ok=True)

    def process_document(self, file_path: str) -> Generator[ProcessingProgress, None, None]:
        try:
            # Upload stage
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting document upload"
            )

            # Upload file using Gemini's built-in file handling
            file_obj = genai.upload_file(file_path)
            
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=100,
                message="Document upload complete"
            )

            # Analysis stage
            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document content"
            )

            # Extract text content using Gemini's document processing
            prompt = '''Extract all text content from this document, properly formatted into paragraphs.
            Return only the clean text content, without any formatting markers, page numbers, or headers.
            Split into natural paragraphs based on content.'''

            response = self.model.generate_content(
                [prompt, file_obj],
                stream=True
            )

            all_paragraphs = []
            for chunk in response:
                if chunk and chunk.text:
                    # Clean and validate chunk text
                    text = chunk.text.strip()
                    if text:
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        all_paragraphs.extend(paragraphs)

                        yield ProcessingProgress(
                            stage=ProcessingStage.PROCESSING,
                            progress=50,  # Approximate progress
                            message=f"Processing content... ({len(all_paragraphs)} paragraphs found)"
                        )

            if not all_paragraphs:
                raise Exception("No valid text content extracted from document")

            # Format story data
            story_data = {
                'paragraphs': [{
                    'text': p,
                    'image_url': None,
                    'audio_url': None
                } for p in all_paragraphs if len(p.strip()) > 0]
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
            # Clean up uploaded file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                self.logger.error(f"Error cleaning up file: {str(e)}")
