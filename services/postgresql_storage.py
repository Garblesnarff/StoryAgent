from flask_sqlalchemy import SQLAlchemy
import base64
from datetime import datetime
import logging

# Import the existing db instance
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PostgresqlStorage:
    def __init__(self, app=None):
        self.app = app

    def init_app(self, app):
        self.app = app
        # We don't need to initialize db here since it's already initialized in app.py
        with app.app_context():
            db.create_all()

    def upload_audio_chunk(self, audio_data, filename):
        try:
            with self.app.app_context():
                audio_file = AudioFile(
                    filename=filename,
                    data=audio_data
                )
                db.session.add(audio_file)
                db.session.commit()
                
                # Return URL to access the audio file
                return f"/audio/{audio_file.id}"
        except Exception as e:
            logging.error(f"Error uploading audio: {str(e)}")
            if db.session:
                db.session.rollback()
            return None
