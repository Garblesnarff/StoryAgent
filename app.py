import os
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
import secrets
from datetime import datetime
from database import db
import logging
import traceback

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
db.init_app(app)

# Initialize services
try:
    from services.book_processor import BookProcessor
    from models import TempBookData
    book_processor = BookProcessor()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Service initialization error: {str(e)}\n{traceback.format_exc()}")
    book_processor = None

# Register blueprints
try:
    from blueprints.story import story_bp
    from blueprints.generation import generation_bp
    app.register_blueprint(story_bp)
    app.register_blueprint(generation_bp)
    logger.info("Blueprints registered successfully")
except Exception as e:
    logger.error(f"Blueprint registration error: {str(e)}\n{traceback.format_exc()}")

# Initialize database tables
with app.app_context():
    try:
        import models
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}\n{traceback.format_exc()}")

@app.route('/')
def index():
    if 'story_data' in session:
        session.pop('story_data', None)
    return render_template('index.html')

@app.route('/story/upload', methods=['POST'])
def upload_story():
    try:
        if 'file' not in request.files:
            logger.error("No file found in request")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            logger.error("Empty filename provided")
            return jsonify({'error': 'No file selected'}), 400

        if not book_processor:
            logger.error("Book processor service not initialized")
            return jsonify({'error': 'Book processing service is not available'}), 500

        # Process the uploaded file
        logger.info(f"Processing uploaded file: {file.filename}")
        result = book_processor.process_file(file)

        if result.get('error'):
            logger.error(f"Error in book processing: {result['error']}")
            return jsonify({'error': result['error']}), 400

        # Store data in session
        session['story_data'] = {
            'temp_id': result['temp_id'],
            'source_file': result['source_file'],
            'paragraphs': result.get('paragraphs', [])
        }

        logger.info(f"Successfully processed file, temp_id: {result['temp_id']}")
        return jsonify({
            'status': 'complete',
            'message': 'Processing complete',
            'progress': 100,
            'redirect': '/story/edit'
        })

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.before_request
def check_story_data():
    if request.path.startswith('/static') or \
       request.path == '/' or \
       request.path == '/generate_story' or \
       request.path == '/story/upload':
        return

    if 'story_data' not in session and \
       (request.path.startswith('/story/') or request.path.startswith('/save')):
        flash('Please generate a story first', 'warning')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'The requested page was not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'An internal server error occurred'}), 500

@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=3000, debug=True)