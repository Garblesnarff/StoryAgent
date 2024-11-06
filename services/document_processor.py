import google.generativeai as genai
import logging
import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, AsyncGenerator
import json
import asyncio

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
        self.model = genai.GenerativeModel('gemini-1.0-pro')
        self.upload_dir = Path('uploads')
        self.upload_dir.mkdir(exist_ok=True)

    async def process_document(self, file_path: str) -> AsyncGenerator[ProcessingProgress, None]:
        """Process document with progress updates"""
        try:
            # Upload stage
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting document upload"
            )

            uploaded_file = genai.upload_file(Path(file_path))
            
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

            # Process document content
            prompt = """Extract the main story content from this document. 
            Break it into distinct paragraphs suitable for narration and visualization.
            For each paragraph:
            1. Clean and format the text
            2. Suggest an image generation prompt
            3. Add narration guidance for voice generation
            
            Format the response as JSON with an array of paragraphs."""

            response = await self.model.generate_content([prompt, uploaded_file])
            
            if not response:
                raise Exception("Failed to process document content")

            try:
                content_data = json.loads(response.text)
            except json.JSONDecodeError:
                # Handle non-JSON response by splitting into paragraphs
                paragraphs = [p.strip() for p in response.text.split('\n\n') if p.strip()]
                content_data = {
                    'paragraphs': [{
                        'text': p,
                        'image_prompt': f"Create an illustrative image for the text: {p}",
                        'narration_guidance': "Narrate with natural pacing and clear enunciation"
                    } for p in paragraphs]
                }

            yield ProcessingProgress(
                stage=ProcessingStage.PROCESSING,
                progress=100,
                message="Document processing complete",
                details={'paragraphs': content_data['paragraphs']}
            )

            # Clean up uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)

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
