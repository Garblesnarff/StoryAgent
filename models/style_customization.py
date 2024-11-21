from database import db
from datetime import datetime

class StyleCustomization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    paragraph_index = db.Column(db.Integer, nullable=False)
    image_style = db.Column(db.String(50))
    mood_enhancement = db.Column(db.String(50))
    voice_style = db.Column(db.String(50))
    text_enhancement = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
