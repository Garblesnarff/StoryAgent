import os
import logging
from typing import Set
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

class ValidationService:
    """Handles validation operations for book processing."""
    
    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {'pdf', 'epub', 'txt', 'html'}
        
    def validate_file(self, file) -> tuple[bool, str, str]:
        """Validate uploaded file and return (is_valid, message, filename)."""
        try:
            if not file:
                return False, "No file provided", ""

            filename = secure_filename(file.filename)
            if not filename or '.' not in filename:
                return False, "Invalid filename", ""

            ext = filename.rsplit('.', 1)[1].lower()
            if ext not in self.allowed_extensions:
                return False, f"Unsupported file type: {ext}", ""

            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            
            if size > self.max_file_size:
                return False, f"File too large. Maximum size is {self.max_file_size/(1024*1024)}MB", ""

            return True, "File is valid", filename
        except Exception as e:
            logger.error(f"File validation failed: {str(e)}")
            return False, f"Validation error: {str(e)}", ""
    
    @staticmethod
    def validate_temp_data(temp_data: dict) -> tuple[bool, str]:
        """Validate temporary book data structure."""
        required_fields = {'source_file', 'title', 'total_chunks', 'current_chunk', 'created_at', 'sections'}
        
        try:
            # Check for required fields
            if not all(field in temp_data for field in required_fields):
                missing = required_fields - set(temp_data.keys())
                return False, f"Missing required fields: {missing}"
            
            # Validate sections
            sections = temp_data.get('sections', [])
            if len(sections) < 2:
                return False, "Invalid sections data: minimum 2 sections required"
                
            # Validate section structure
            for section in sections:
                if not all(key in section for key in ['title', 'chunks', 'index']):
                    return False, "Invalid section structure"
                    
            return True, "Data structure is valid"
        except Exception as e:
            logger.error(f"Temp data validation failed: {str(e)}")
            return False, f"Validation error: {str(e)}"
