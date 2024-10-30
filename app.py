import os
from flask import Flask, render_template, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import secrets

from services.text_generator import TextGenerator

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = secrets.token_hex(16)  # Add secret key for session management
db.init_app(app)
socketio = SocketIO(app)

# Initialize services
text_service = TextGenerator()

# Register blueprints
from blueprints.story import story_bp
from blueprints.generation import generation_bp

app.register_blueprint(story_bp)
app.register_blueprint(generation_bp)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        prompt = request.form.get('prompt')
        genre = request.form.get('genre')
        mood = request.form.get('mood')
        target_audience = request.form.get('target_audience')
        num_paragraphs = int(request.form.get('paragraphs', 5))
        
        # Generate story paragraphs
        story_paragraphs = text_service.generate_story(
            prompt, genre, mood, target_audience, num_paragraphs)
            
        if not story_paragraphs:
            return jsonify({'error': 'Failed to generate story'}), 500
            
        # Store story data in session
        session['story_data'] = {
            'prompt': prompt,
            'genre': genre,
            'mood': mood,
            'target_audience': target_audience,
            'paragraphs': [{'text': p, 'image_url': None, 'audio_url': None} for p in story_paragraphs]
        }
        
        return jsonify({'success': True, 'redirect': '/story/edit'})
        
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic
    return jsonify({'success': True})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
