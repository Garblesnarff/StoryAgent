import os
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
import secrets
from datetime import datetime
from database import db
import logging

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = secrets.token_hex(16)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db.init_app(app)

# Initialize services
from services.text_generator import TextGenerator
from services.book_processor import BookProcessor
text_service = TextGenerator()
book_processor = BookProcessor()

# Register blueprints
from blueprints.story import story_bp
from blueprints.generation import generation_bp

app.register_blueprint(story_bp)
app.register_blueprint(generation_bp)

with app.app_context():
    import models
    db.create_all()

def init_sample_story():
    """Initialize sample story data for testing"""
    return {
        'prompt': 'Test story',
        'genre': 'fantasy',
        'mood': 'happy',
        'target_audience': 'young_adult',
        'created_at': str(datetime.now()),
        'paragraphs': [
            {
                'text': 'This is a test paragraph one with some sample text to demonstrate the customization system.',
                'image_style': 'realistic',
                'image_url': None,
                'voice_style': 'neutral'
            },
            {
                'text': 'This is another test paragraph that will help us verify the node-based customization interface.',
                'image_style': 'artistic',
                'image_url': None,
                'voice_style': 'dramatic'
            }
        ]
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        # Validate form data
        required_fields = ['prompt', 'genre', 'mood', 'target_audience']
        for field in required_fields:
            if not request.form.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

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
            
        # Store story data in session with metadata
        session['story_data'] = {
            'prompt': prompt,
            'genre': genre,
            'mood': mood,
            'target_audience': target_audience,
            'created_at': str(datetime.now()),
            'paragraphs': [{'text': p, 'image_url': None, 'audio_url': None} for p in story_paragraphs]
        }
        
        return jsonify({'success': True, 'redirect': '/story/edit'})
        
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    if 'story_data' not in session:
        return jsonify({'error': 'No story data found'}), 404
        
    try:
        # TODO: Implement story saving logic to database
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'The requested page was not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'An internal server error occurred'}), 500

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Please start by creating a new story on the home page'}), 403

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.before_request
def check_story_data():
    # Skip checks for static files and allowed routes
    if (request.path.startswith('/static') or 
        request.path == '/' or 
        request.path == '/generate_story' or 
        request.path == '/story/upload' or
        request.path.startswith('/story/customize')):
        return
    
    # Check if we need story data for story-related routes
    if request.path.startswith('/story/'):
        if 'story_data' not in session:
            if request.path == '/story/customize':
                session['story_data'] = init_sample_story()
                logger.info("Initialized sample story data for customize page")
            else:
                return jsonify({'error': 'Please generate a story first'}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
