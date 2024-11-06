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
            file_size = os.path.getsize(file_path)
            file_type = Path(file_path).suffix
            self.logger.info(f"Starting document processing: {file_path} (size: {file_size} bytes, type: {file_type})")
            
            # Upload stage
            yield ProcessingProgress(
                stage=ProcessingStage.UPLOADING,
                progress=0,
                message="Starting file upload"
            )
            
            self.logger.info(f"Uploading file to Gemini API: {file_path}")
            uploaded_file = genai.upload_file(Path(file_path))
            self.logger.info(f"File uploaded successfully: {uploaded_file.name}")
            
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
            self.logger.info("Starting content extraction")

            # Extract text content using Gemini with copyright-safe prompt
            prompt = '''Extract and summarize the main themes and content from this document.
            Focus on describing the content rather than direct extraction.
            Do not quote directly from the text.
            Return a high-level overview of:
            - Main themes and ideas
            - General structure
            - Key events or concepts
            Format as clean paragraphs without any markers or labels.'''

            self.logger.info("Sending content extraction request to Gemini API")
            response = self.model.generate_content([prompt, uploaded_file])
            self.logger.info("Received response from Gemini API")
            
            try:
                text = response.text
            except ValueError as ve:
                if 'finish_reason is 4' in str(ve):
                    self.logger.info("Detected copyrighted content, offering summary option")
                    yield ProcessingProgress(
                        stage=ProcessingStage.ERROR,
                        progress=0,
                        message="This appears to be copyrighted material. For copyright protection, we can only provide a high-level summary rather than the full text.",
                        details={"error_type": "copyright", "can_summarize": True}
                    )
                    return
                raise
            
            # Split into paragraphs and clean
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            self.logger.info(f"Extracted {len(paragraphs)} paragraphs from document")
            
            if not paragraphs:
                raise Exception("No valid text content extracted from document")

            # Format response data
            processed_data = {
                'paragraphs': [{
                    'text': p
                } for p in paragraphs if len(p.strip()) > 0]
            }
            self.logger.info(f"Processing complete: {len(processed_data['paragraphs'])} valid paragraphs")

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Processing complete",
                details=processed_data
            )

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}", exc_info=True)
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise

    def summarize_document(self, file_path: str) -> Generator[ProcessingProgress, None, None]:
        """
        Generate a high-level summary for copyrighted content
        """
        try:
            self.logger.info(f"Starting document summary: {file_path}")
            
            yield ProcessingProgress(
                stage=ProcessingStage.ANALYZING,
                progress=0,
                message="Analyzing document for summary"
            )

            uploaded_file = genai.upload_file(Path(file_path))
            
            summary_prompt = '''Provide a high-level summary of this document's content.
            Focus on general themes, structure, and key concepts.
            Do not include any direct quotes or specific text.
            Format the summary as 2-3 concise paragraphs.'''
            
            response = self.model.generate_content([summary_prompt, uploaded_file])
            
            if not response or not response.text:
                raise Exception("Failed to generate summary")
                
            summary_text = response.text.strip()
            paragraphs = [p.strip() for p in summary_text.split('\n\n') if p.strip()]
            
            processed_data = {
                'paragraphs': [{
                    'text': f"Summary: {p}"
                } for p in paragraphs if len(p.strip()) > 0]
            }

            yield ProcessingProgress(
                stage=ProcessingStage.COMPLETE,
                progress=100,
                message="Summary generation complete",
                details=processed_data
            )

        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}", exc_info=True)
            yield ProcessingProgress(
                stage=ProcessingStage.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )
            raise
