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
    progress: float  # 0-100
    message: str
    details: Dict = None

class DocumentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
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
            
            # Read file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
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

            # Process content with Gemini - Fixed API call
            prompt = "Extract and clean text from this document, split into paragraphs."
            response = self.model.generate_content([prompt, content])
            
            if not response or not response.text:
                raise Exception("Failed to process document content")

            # Clean and validate the extracted text
            text = response.text.strip()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            if not paragraphs:
                raise Exception("No valid text content found in document")

            # Format paragraphs for story generation
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
