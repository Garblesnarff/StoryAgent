from database import db
from datetime import datetime
import uuid
from typing import Dict, Any

class TempBookData(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = db.Column(db.JSON) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def total_chunks(self) -> int:
        """Get total number of chunks in the book data"""
        return len(self.data.get('paragraphs', [])) if self.data else 0

    @property
    def chunk_size(self) -> int:
        """Get chunk size (number of sentences per chunk)"""
        return self.data.get('chunk_size', 2) if self.data else 2

    @property
    def chunks_per_page(self) -> int:
        """Get number of chunks per page"""
        return self.data.get('chunks_per_page', 10) if self.data else 10

    def get_page(self, page_number: int) -> Dict[str, Any]:
        """Get chunks for a specific page"""
        if not self.data or 'paragraphs' not in self.data:
            return {'chunks': [], 'total_pages': 0, 'current_page': page_number}

        start_idx = (page_number - 1) * self.chunks_per_page
        end_idx = start_idx + self.chunks_per_page
        total_pages = (self.total_chunks + self.chunks_per_page - 1) // self.chunks_per_page

        chunks = self.data['paragraphs'][start_idx:end_idx]
        return {
            'chunks': chunks,
            'total_pages': total_pages,
            'current_page': page_number,
            'total_chunks': len(chunks),
            'chunks_per_page': self.chunks_per_page
        }

    @classmethod
    def create_from_data(cls, book_data: Dict[str, Any]) -> 'TempBookData':
        """Create a new TempBookData instance with initialized data structure"""
        data = {
            'source_file': book_data.get('source_file', ''),
            'paragraphs': book_data.get('paragraphs', []),
            'chunk_size': 2,
            'chunks_per_page': 10,
            'total_chunks': len(book_data.get('paragraphs', [])),
            'current_page': 1
        }
        return cls(data=data)