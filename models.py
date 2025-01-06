from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    audio_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now())

class TempBookData(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_page(self, page_number, items_per_page=10):
        """Get a specific page of paragraphs from the book data"""
        if not self.data or 'paragraphs' not in self.data:
            return None

        paragraphs = self.data['paragraphs']
        total_paragraphs = len(paragraphs)
        total_pages = (total_paragraphs + items_per_page - 1) // items_per_page

        if page_number < 1 or page_number > total_pages:
            return None

        start_idx = (page_number - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_paragraphs)

        return {
            'paragraphs': paragraphs[start_idx:end_idx],
            'current_page': page_number,
            'total_pages': total_pages,
            'total_paragraphs': total_paragraphs,
            'items_per_page': items_per_page
        }

class StyleCustomization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    paragraph_index = db.Column(db.Integer, nullable=False)
    image_style = db.Column(db.String(50))
    mood_enhancement = db.Column(db.String(50))
    voice_style = db.Column(db.String(50))
    text_enhancement = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)