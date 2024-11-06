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

            # Add prompt to ensure proper text extraction and formatting
            prompt = '''Extract clean, readable text from this document and format as paragraphs. 
            Return the text without any markup, headers, or special characters.
            Split into natural paragraphs based on content breaks.'''

            response = self.model.generate_content([prompt, content])
            
            if not response or not response.text:
                raise Exception("Failed to process document content")

            # Clean and validate response text
            cleaned_text = response.text.strip()
            # Split into paragraphs and remove empty ones
            paragraphs = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
            
            if not paragraphs:
                raise Exception("No valid text content found in document")

            content_data = {
                'paragraphs': [{
                    'text': p,
                    'image_prompt': f"Create an illustrative image for: {p[:100]}..." if len(p) > 0 else "Create a generic illustration",
                    'narration_guidance': "Narrate naturally with clear enunciation"
                } for p in paragraphs if len(p.strip()) > 0]
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
