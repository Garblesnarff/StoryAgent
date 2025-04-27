from database import db
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

class GenerationHistory(db.Model):
    """Stores history of media generation attempts (images, audio)."""
    __tablename__ = 'generation_history'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    temp_data_id = db.Column(UUID(as_uuid=True), db.ForeignKey('temp_book_data.id'), nullable=False, index=True)
    paragraph_index = db.Column(db.Integer, nullable=False, index=True)
    generation_type = db.Column(db.String(50), nullable=False) # e.g., 'image', 'audio'
    status = db.Column(db.String(50), nullable=False) # e.g., 'success', 'failed'
    error_message = db.Column(db.Text, nullable=True)
    prompt = db.Column(db.Text, nullable=True)
    result_url = db.Column(db.Text, nullable=True) # Store URL or identifier for the generated media
    retries = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship (optional but good practice)
    temp_book_data = db.relationship('TempBookData', backref=db.backref('generation_history_entries', lazy=True))

    def __repr__(self):
        return f"<GenerationHistory(id={self.id}, temp_id={self.temp_data_id}, index={self.paragraph_index}, type='{self.generation_type}', status='{self.status}')>"
