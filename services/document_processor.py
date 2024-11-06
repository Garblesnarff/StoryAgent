import google.generativeai as genai
import logging
import json
from typing import List, Dict, Generator, AsyncGenerator
import os
from pathlib import Path
import asyncio
from dataclasses import dataclass
from enum import Enum
import time

class ProcessingStage(Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    EXTRACTING_METADATA = "extracting_metadata"
    PROCESSING_CHAPTERS = "processing_chapters"
    ENHANCING_CONTENT = "enhancing_content"
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
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash-8b')
        self.logger = logging.getLogger(__name__)

    def process_document(self, file_path: str) -> Generator[ProcessingProgress, None, None]:
        """
        Synchronous document processing method that yields progress updates
        """
        try:
            # Upload file
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting file upload"
            )
            
            uploaded_file = genai.upload_file(Path(file_path))
            
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=100,
                message="Document upload complete"
            )

            # Process document content
            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document content"
            )

            # Extract text content using Gemini
            prompt = '''Extract clean, readable text from this document, properly formatted into paragraphs.
            Remove any headers, footers, page numbers, and formatting markers.
            Split text into natural paragraphs based on content breaks.
            Return only the cleaned text content.'''

            response = self.model.generate_content([prompt, uploaded_file])
            
            if not response or not response.text:
                raise Exception("Failed to extract content from document")

            # Split into paragraphs and clean
            text = response.text.strip()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            if not paragraphs:
                raise Exception("No valid text content extracted from document")

            # Format response data
            processed_data = {
                'paragraphs': [{
                    'text': p
                } for p in paragraphs if len(p.strip()) > 0]
            }

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Processing complete",
                details=processed_data
            )

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise

    async def process_document_streaming(
        self, file_path: str
    ) -> AsyncGenerator[ProcessingProgress, None]:
        """
        Process document with progress updates and streaming results
        Returns an async generator of ProcessingProgress objects
        """
        try:
            # Upload file
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting file upload"
            )

            uploaded_file = genai.upload_file(Path(file_path))

            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=100,
                message="File upload complete",
                details={"file_name": uploaded_file.name}
            )

            # Initial metadata extraction
            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document structure"
            )

            # Extract text content using Gemini
            prompt = '''Extract clean, readable text from this document, properly formatted into paragraphs.
            Remove any headers, footers, page numbers, and formatting markers.
            Split text into natural paragraphs based on content breaks.
            Return only the cleaned text content.'''

            response = await self.model.generate_content([prompt, uploaded_file])
            
            if not response or not response.text:
                raise Exception("Failed to extract content from document")

            # Split into paragraphs and clean
            text = response.text.strip()
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            if not paragraphs:
                raise Exception("No valid text content extracted from document")

            # Format response data
            processed_data = {
                'paragraphs': [{
                    'text': p
                } for p in paragraphs if len(p.strip()) > 0]
            }

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Processing complete",
                details=processed_data
            )

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise
