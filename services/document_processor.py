import google.generativeai as genai
import os
import logging
import json
from typing import Dict
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
        
        # Create uploads directory if it doesn't exist
        self.upload_dir = 'uploads'
        os.makedirs(self.upload_dir, exist_ok=True)

    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            self.logger.error(f"Error reading PDF file: {str(e)}")
            raise ValueError(f"Failed to read PDF file: {str(e)}")

    def _read_epub(self, file_path: str) -> str:
        """Extract text from EPUB file"""
        try:
            book = epub.read_epub(file_path)
            text = ""
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text() + "\n"
            return text
        except Exception as e:
            self.logger.error(f"Error reading EPUB file: {str(e)}")
            raise ValueError(f"Failed to read EPUB file: {str(e)}")

    def _read_html(self, file_path: str) -> str:
        """Extract text from HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                return soup.get_text()
        except Exception as e:
            self.logger.error(f"Error reading HTML file: {str(e)}")
            raise ValueError(f"Failed to read HTML file: {str(e)}")

    def _process_text_chunk(self, text: str) -> Dict:
        """Process a chunk of text using Gemini"""
        try:
            prompt = f"""Analyze this text and return a JSON response in exactly this format:
            {{
                "metadata": {{
                    "title": "string",
                    "author": "string",
                    "genre": "string"
                }},
                "chapters": [
                    {{
                        "number": 1,
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

            Text to analyze:
            {text}
            """

            response = self.model.generate_content(prompt)
            
            # Extract the response text
            response_text = response.text if hasattr(response, 'text') else response.parts[0].text
            
            # Find JSON content
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON content found in response")
                
            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)

            # Validate structure
            if 'metadata' not in result or 'chapters' not in result:
                raise ValueError("Invalid response format")

            return result

        except Exception as e:
            self.logger.error(f"Error processing text chunk: {str(e)}")
            raise

    def process_document(self, file_path: str, file_type: str) -> Dict:
        """Process a document and return structured content"""
        try:
            # Read document
            if file_type == 'pdf':
                text = self._read_pdf(file_path)
            elif file_type == 'epub':
                text = self._read_epub(file_path)
            elif file_type == 'html':
                text = self._read_html(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Process text in chunks if needed
            chunk_size = 2000  # Process 2000 chars at a time
            if len(text) > chunk_size:
                chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                results = []
                for chunk in chunks:
                    try:
                        chunk_result = self._process_text_chunk(chunk)
                        results.append(chunk_result)
                    except Exception as e:
                        self.logger.warning(f"Error processing chunk: {str(e)}")
                        continue

                # Merge results
                final_result = results[0]  # Use first chunk's metadata
                all_chapters = []
                for r in results:
                    all_chapters.extend(r.get('chapters', []))
                final_result['chapters'] = all_chapters
                return final_result

            else:
                return self._process_text_chunk(text)

        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            raise
