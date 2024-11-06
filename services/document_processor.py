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
        """Process document with progress updates"""
        try:
            # Upload stage
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting document upload"
            )

            # Use synchronous file upload
            with open(file_path, 'rb') as f:
                content = f.read()
                
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=100,
                message="Document upload complete"
            )

            # Process content synchronously
            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document content"
            )

            response = self.model.generate_content(
                ["Extract and clean the text content from this document, split into paragraphs.", content]
            )
            
            if not response:
                raise Exception("Failed to process document content")

            # Parse response and format paragraphs
            paragraphs = [p.strip() for p in response.text.split('\n\n') if p.strip()]
            content_data = {
                'paragraphs': [{
                    'text': p,
                    'image_prompt': f"Create an illustrative image for: {p[:100]}...",
                    'narration_guidance': "Narrate naturally with clear enunciation"
                } for p in paragraphs]
            }

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Processing complete",
                details=content_data
            )

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise
