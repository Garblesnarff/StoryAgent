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
            'current_position': result['current_position']
        }
        session.modified = True

        logger.info(f"Successfully processed file, temp_id: {result['temp_id']}")
        return jsonify({
            'success': True,
            'message': 'File processed successfully'
        })

    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/story/load_more', methods=['POST'])
def load_more_chunks():
    """Load the next batch of chunks."""
    try:
        if 'story_data' not in session:
            logger.error("No story data found in session")
            return jsonify({'error': 'No story data found'}), 404

        temp_id = session['story_data'].get('temp_id')
        if not temp_id:
            logger.error("No temp_id found in session")
            return jsonify({'error': 'Invalid session data'}), 400

        # Get stored data
        temp_data = TempBookData.query.get(temp_id)
        if not temp_data:
            logger.error(f"No data found for temp_id: {temp_id}")
            return jsonify({'error': 'Data not found'}), 404

        current_position = session['story_data'].get('current_position', 0)
        total_chunks = len(temp_data.data['paragraphs'])

        if current_position >= total_chunks:
            logger.info("No more chunks available")
            return jsonify({
                'success': True,
                'message': 'No more chunks available',
                'current_position': current_position,
                'total_chunks': total_chunks
            })

        # Get next batch of paragraphs
        next_batch_size = min(10, total_chunks - current_position)
        next_position = current_position + next_batch_size
        next_paragraphs = temp_data.data['paragraphs'][current_position:next_position]

        # Update session
        session['story_data']['current_position'] = next_position
        session.modified = True

        logger.info(f"Loaded chunks {current_position} to {next_position} of {total_chunks}")
        return jsonify({
            'success': True,
            'paragraphs': next_paragraphs,
            'start_index': current_position,
            'current_position': next_position,
            'total_chunks': total_chunks
        })

    except Exception as e:
        logger.error(f"Error loading more chunks: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.before_request
def check_story_data():
    if request.path.startswith('/static') or \
       request.path == '/' or \
       request.path == '/generate_story' or \
       request.path == '/story/upload' or \
       request.path == '/story/load_more':
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
    app.run(host='0.0.0.0', port=5001, debug=True)