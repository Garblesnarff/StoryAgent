import google.generativeai as genai
import os
import logging
import json
from typing import Dict, List
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import PyPDF2

class DocumentProcessor:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.logger = logging.getLogger(__name__)

    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _read_epub(self, file_path: str) -> str:
        """Extract text from EPUB file"""
        book = epub.read_epub(file_path)
        text = ""
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            text += soup.get_text() + "\n"
        return text

    def _read_html(self, file_path: str) -> str:
        """Extract text from HTML file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            return soup.get_text()

    def process_document(self, file_path: str, file_type: str) -> Dict:
        """Process document using Gemini"""
        try:
            # Read the document based on type
            if file_type == 'pdf':
                raw_text = self._read_pdf(file_path)
            elif file_type == 'epub':
                raw_text = self._read_epub(file_path)
            elif file_type == 'html':
                raw_text = self._read_html(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Process with Gemini
            prompt = f"""Analyze this book text and:
            1. Split it into well-formed paragraphs
            2. Remove any headers, footers, page numbers, and formatting artifacts
            3. Identify chapter breaks
            4. Extract book metadata (title, author, etc.) if present
            5. Return the results in this JSON format:
            {{
                "metadata": {{
                    "title": "string",
                    "author": "string",
                    "year": "string",
                    "genre": "string"
                }},
                "chapters": [
                    {{
                        "number": int,
                        "title": "string",
                        "paragraphs": [
                            {{
                                "text": "string",
                                "suggested_image_prompt": "string"
                            }}
                        ]
                    }}
                ]
            }}

            Text to process:
            {raw_text[:1000]}"""  # Process first 1000 chars as example

            response = self.model.generate_content(prompt)
            
            try:
                result = json.loads(response.text)
                self.logger.info(f"Successfully processed document with {len(result['chapters'])} chapters")
                return result
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Gemini response as JSON")
                raise

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            raise

    def enhance_paragraph_prompts(self, text: str) -> Dict[str, str]:
        """Generate enhanced image and audio prompts for a paragraph"""
        try:
            prompt = f"""Analyze this paragraph and provide:
            1. A detailed image generation prompt that captures the key visual elements
            2. Guidance for audio narration (tone, emotion, pacing)
            
            Return as JSON with these keys: "image_prompt", "audio_guidance"

            Paragraph:
            {text}
            """

            response = self.model.generate_content(prompt)
            return json.loads(response.text)

        except Exception as e:
            self.logger.error(f"Error enhancing paragraph prompts: {str(e)}")
            return {
                "image_prompt": text,
                "audio_guidance": "Narrate with a natural, clear tone"
            }
