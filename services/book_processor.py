import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
from werkzeug.utils import secure_filename
from database import db
from models import TempBookData
from services.text.text_extractor import TextExtractor
from services.text.text_cleaner import TextCleaner
from services.text.text_chunker import TextChunker
from services.text.title_extractor import TitleExtractor
from services.text.validation_service import ValidationService

logger = logging.getLogger(__name__)

class BookProcessor:
    """Orchestrates the book processing workflow using specialized services."""
    
    def __init__(self):
        self.text_extractor = TextExtractor()
        self.text_cleaner = TextCleaner()
        self.text_chunker = TextChunker()
        self.title_extractor = TitleExtractor()
        self.validation_service = ValidationService()

    def process_file(self, file) -> Dict[str, any]:
        """Process uploaded file using specialized services."""
        try:
            # Validate file
            is_valid, message, filename = self.validation_service.validate_file(file)
            if not is_valid:
                raise ValueError(message)

            # Save file temporarily
            temp_path = os.path.join('uploads', filename)
            os.makedirs('uploads', exist_ok=True)
            file.save(temp_path)

            try:
                # Extract text based on file type
                ext = filename.rsplit('.', 1)[1].lower()
                text = self.text_extractor.extract_text(temp_path, ext)

                # Clean and process text
                text = self.text_cleaner.clean_text(text)
                title = self.title_extractor.extract_title(text)
                story_text = self.text_cleaner.extract_story_content(text)
                
                # Create chunks
                sentences = self.text_chunker.split_into_sentences(story_text)
                chunks = self.text_chunker.create_chunks(sentences)

                # Create sections
                temp_id = str(uuid.uuid4())
                title_section = {
                    'title': 'Book Title',
                    'chunks': [{
                        'text': title,
                        'image_url': None,
                        'audio_url': None,
                        'is_title': True
                    }],
                    'index': 0,
                    'processed': True
                }
                
                content_section = {
                    'title': 'Story Content',
                    'chunks': chunks,
                    'index': 1,
                    'processed': False
                }
                
                # Prepare story data
                story_data = {
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(chunks),
                    'current_chunk': 0,
                    'created_at': str(datetime.utcnow()),
                    'sections': [title_section, content_section]
                }

                # Validate and save temporary data
                is_valid, validation_message = self.validation_service.validate_temp_data(story_data)
                if not is_valid:
                    raise ValueError(validation_message)

                try:
                    temp_data = TempBookData(id=temp_id, data=story_data)
                    db.session.add(temp_data)
                    db.session.commit()
                    logger.info(f"Successfully processed book - ID: {temp_id}, Title: {title}")
                except Exception as db_error:
                    logger.error(f"Database error - ID: {temp_id}")
                    db.session.rollback()
                    raise

                return {
                    'temp_id': temp_id,
                    'source_file': filename,
                    'title': title,
                    'total_chunks': len(chunks),
                    'current_page': 1,
                    'chunks_per_page': 50
                }

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise

    def get_next_section(self, temp_id: str, page: int = 1, chunks_per_page: int = 50) -> Optional[Dict]:
        """Get chunks for the specified page with pagination."""
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data or not temp_data.data:
            logger.error(f"No temp data found for ID: {temp_id}")
            return None

        book_data = temp_data.data
        sections = book_data.get('sections', [])
        
        if not sections or len(sections) < 2:
            logger.error(f"Invalid sections data for ID: {temp_id}")
            return None
            
        # Always include title section
        title_section = sections[0]
        title_chunks = title_section.get('chunks', [])
        
        # Get content chunks from second section
        content_section = sections[1]
        content_chunks = content_section.get('chunks', [])

        total_content_chunks = len(content_chunks)
        start_idx = (page - 1) * chunks_per_page
        end_idx = min(start_idx + chunks_per_page, total_content_chunks)

        if start_idx >= total_content_chunks:
            logger.warning(f"Requested page {page} exceeds available chunks")
            return None

        # Get content chunks for current page
        current_chunks = content_chunks[start_idx:end_idx]
        
        # Always include title chunks at the beginning of first page
        if page == 1:
            current_chunks = title_chunks + current_chunks
        
        logger.info(f"Serving page {page}/{(total_content_chunks + chunks_per_page - 1) // chunks_per_page}")
        
        return {
            'chunks': current_chunks,
            'current_page': page,
            'total_pages': (total_content_chunks + chunks_per_page - 1) // chunks_per_page,
            'has_next': end_idx < total_content_chunks,
            'title': book_data.get('title')
        }