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
from models import TempBookData
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

@app.route('/')
def index():
    # Clear any existing story data when returning to home
    if 'story_data' in session:
        session.pop('story_data', None)
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    try:
        # Validate form data
        required_fields = ['prompt', 'genre', 'mood', 'target_audience']
        for field in required_fields:
            if not request.form.get(field):
                logger.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400

        prompt = request.form.get('prompt')
        genre = request.form.get('genre')
        mood = request.form.get('mood')
        target_audience = request.form.get('target_audience')
        num_paragraphs = int(request.form.get('paragraphs', 5))
        
        logger.info(f"Generating story with prompt: {prompt[:50]}...")
        # Generate story paragraphs
        story_paragraphs = text_service.generate_story(
            prompt, genre, mood, target_audience, num_paragraphs)
            
        if not story_paragraphs:
            logger.error("Failed to generate story paragraphs")
            return jsonify({'error': 'Failed to generate story'}), 500
            
        # Create story data structure
        story_data = {
            'prompt': prompt,
            'genre': genre,
            'mood': mood,
            'target_audience': target_audience,
            'created_at': str(datetime.now()),
            'paragraphs': [{'text': p, 'image_url': None, 'audio_url': None, 'image_style': 'realistic'} for p in story_paragraphs]
        }
        
        # Create a new TempBookData entry with UUID
        temp_data = TempBookData(data=story_data)
        
        try:
            db.session.add(temp_data)
            db.session.commit()
            logger.info(f"Saved story data with temp_id: {temp_data.id}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {str(db_error)}")
            return jsonify({'error': 'Failed to save story data'}), 500
        
        # Store story data in session
        session['story_data'] = {
            'temp_id': temp_data.id,
            'story_context': '\n\n'.join(story_paragraphs),
            'paragraphs': story_data['paragraphs']
        }
        session.modified = True
        
        logger.info("Story generation successful, redirecting to edit page")
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
    flash('Please start by creating a new story on the home page', 'warning')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.before_request
def check_story_data():
    # Skip checks for static files and allowed routes
    if request.path.startswith('/static') or \
       request.path == '/' or \
       request.path == '/generate_story' or \
       request.path == '/story/upload':  # Add upload route to exclusions
        return
        
    # Check if story data exists for protected routes
    if 'story_data' not in session and \
       (request.path.startswith('/story/') or request.path.startswith('/save')):
        flash('Please generate a story first', 'warning')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
