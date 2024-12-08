import os
import sys
import time
import atexit
import socket
import psutil
import logging
import secrets
from datetime import datetime
from flask import (
    Flask, render_template, request, session,
    jsonify, redirect, url_for, flash,
    send_from_directory, Response, stream_with_context
)
from flask_cors import CORS
from database import db
from config import Config
from services.text_generator import TextGenerator
from services.book_processor import BookProcessor
from services.text import (
    TextExtractor, TextCleaner, TextChunker,
    TitleExtractor, ValidationService
)
from models import TempBookData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag to track server status
SERVER_RUNNING = False

def create_app():
    """Create and configure the Flask application instance"""
    """Create and configure the Flask application"""
    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.secret_key = secrets.token_hex(16)
    
    # Create route handlers
    @app.route('/')
    def index():
        # Clear any existing story data when returning to home
        if 'story_data' in session:
            session.pop('story_data', None)
        return render_template('index.html')

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
           request.path == '/story/upload':
            return
            
        # Check if story data exists for protected routes
        if 'story_data' not in session and \
           (request.path.startswith('/story/') or request.path.startswith('/save')):
            flash('Please generate a story first', 'warning')
            return redirect(url_for('index'))

    # Configure upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    MAX_RESPONSE_LENGTH = 1 * 1024 * 1024  # 1MB max response size
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['MAX_RESPONSE_LENGTH'] = MAX_RESPONSE_LENGTH
    app.config['CORS_HEADERS'] = 'Content-Type'

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Initialize database
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

    # Initialize services
    from services.text_generator import TextGenerator
    from services.book_processor import BookProcessor
    from models import TempBookData
    from services.text import (
        TextExtractor, TextCleaner, TextChunker,
        TitleExtractor, ValidationService
    )

    # Initialize service instances
    app.text_service = TextGenerator()
    app.book_processor = BookProcessor(upload_dir='uploads')

    # Import and register blueprints
    with app.app_context():
        from blueprints.story import story_bp
        from blueprints.generation import generation_bp
        app.register_blueprint(story_bp)
        app.register_blueprint(generation_bp)

    # Additional route for generating stories
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
            story_paragraphs = app.text_service.generate_story(
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
            from models import TempBookData
            temp_data = TempBookData(data=story_data)
            
            try:
                db.session.add(temp_data)
                db.session.commit()
                logger.info(f"Saved story data with temp_id: {temp_data.id}")
            except Exception as db_error:
                db.session.rollback()
                logger.error(f"Database error: {str(db_error)}")
                return jsonify({'error': 'Failed to save story data'}), 500
            
            # Store only essential metadata in session
            session['story_data'] = {
                'temp_id': temp_data.id,
                'current_page': 1,
                'total_pages': len(story_paragraphs) // 10 + (1 if len(story_paragraphs) % 10 > 0 else 0)
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
            
    return app

# Create the application instance
app = create_app()

def cleanup():
    """Cleanup function to ensure resources are properly released"""
    logger.info("Cleaning up server resources...")
    
    # Skip cleanup in reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        return
        
    try:
        # Get current process info
        current_pid = os.getpid()
        logger.info(f"Cleanup initiated by process {current_pid}")
        
        # Clean up any processes using our port
        port_in_use = True
        max_attempts = 3
        attempt = 0
        
        while port_in_use and attempt < max_attempts:
            attempt += 1
            logger.info(f"Cleanup attempt {attempt}/{max_attempts}")
            
            # Try to kill any process using our port
            kill_existing_process()
            time.sleep(1)  # Wait for process termination
            
            # Check if port is now available
            port_in_use = not is_port_available(Config.PORT)
            if port_in_use and attempt < max_attempts:
                logger.warning(f"Port {Config.PORT} still in use after attempt {attempt}")
            elif not port_in_use:
                logger.info(f"Port {Config.PORT} successfully freed")
            else:
                logger.error(f"Failed to free port {Config.PORT} after {max_attempts} attempts")
                
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
    finally:
        logger.info("Cleanup process completed")

def kill_existing_process():
    """Kill any process using the configured port"""
    try:
        port = Config.PORT
        current_pid = os.getpid()
        
        for conn in psutil.net_connections():
            try:
                if (hasattr(conn, 'laddr') and 
                    conn.laddr.port == port and 
                    conn.status == 'LISTEN' and 
                    conn.pid != current_pid):  # Don't kill ourselves
                    
                    try:
                        proc = psutil.Process(conn.pid)
                        # Try graceful termination first
                        proc.terminate()
                        logger.info(f"Attempting to terminate process {conn.pid} using port {port}")
                        
                        # Wait for process to terminate
                        try:
                            proc.wait(timeout=3)
                            logger.info(f"Successfully terminated process {conn.pid}")
                        except psutil.TimeoutExpired:
                            # If graceful termination fails, force kill
                            logger.warning(f"Process {conn.pid} didn't terminate gracefully, forcing kill")
                            proc.kill()
                            proc.wait(timeout=1)
                            logger.info(f"Forcefully killed process {conn.pid}")
                            
                    except (ProcessLookupError, PermissionError, psutil.NoSuchProcess):
                        logger.warning(f"Process {conn.pid} no longer exists or permission denied")
                    except Exception as kill_error:
                        logger.error(f"Error killing process {conn.pid}: {str(kill_error)}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error) as e:
                logger.debug(f"Error accessing process: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error checking for existing processes: {str(e)}")

def is_port_available(port):
    """Check if a port is available"""
    sock = None
    try:
        # Create socket with address reuse
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Try to bind to the port
        sock.bind(('0.0.0.0', port))
        sock.listen(1)
        sock.close()
        return True
        
    except socket.error as e:
        logger.warning(f"Port {port} is not available: {str(e)}")
        return False
        
    finally:
        if sock:
            try:
                sock.close()
            except socket.error:
                pass

if __name__ == "__main__":
    try:
        # Only perform initialization in the main process
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            logger.info("Starting main process...")
            
            # Register cleanup handler for graceful shutdown
            atexit.register(cleanup)
            
            # Perform initial cleanup
            cleanup()
            
            # Final port check before starting
            if not is_port_available(Config.PORT):
                logger.error(f"Port {Config.PORT} is still in use after cleanup")
                sys.exit(1)
            
            logger.info(f"Port {Config.PORT} is available, starting server")
        
        # Set server running flag
        SERVER_RUNNING = True
        
        # Configure server
        logger.info(f"Starting Flask server on {Config.HOST}:{Config.PORT}")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=False,  # Disable debug mode
            use_reloader=False,  # Prevent duplicate processes
            threaded=True,  # Enable threading
            use_debugger=False  # Disable debugger
        )
        
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        if SERVER_RUNNING:
            cleanup()  # Ensure cleanup runs if server was partially started
        sys.exit(1)
