"""
Story Generation Web Application

This Flask application serves as the backend for an AI-powered story generation platform.
It provides endpoints for story creation, customization, and management, integrating
various AI services for text generation, image creation, and audio synthesis.

The application uses a multi-agent architecture to handle different aspects of story
generation, including concept generation, world building, and plot development.

Features:
- Story generation with customizable parameters
- Node-based story customization
- Document processing (PDF, EPUB, HTML)
- Image and audio generation
- Session-based story management
"""

import os
import secrets
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union

from flask import (
    Flask, 
    render_template, 
    request, 
    session, 
    jsonify, 
    redirect, 
    url_for, 
    flash,
    Response
)
from database import db

# Initialize Flask application
app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = secrets.token_hex(16)

# Application Constants
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

# Configure application settings
def configure_app(app: Flask) -> None:
    """Configure application settings and environment.
    
    Sets up critical application configuration including:
    - File upload directory and size limits
    - Static file paths
    - Security settings
    
    Args:
        app (Flask): The Flask application instance to configure
        
    Returns:
        None
        
    Raises:
        OSError: If upload directory creation fails
    """
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config.update(
        UPLOAD_FOLDER=UPLOAD_FOLDER,
        MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
        # Enforce HTTPS in production
        SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
        # Prevent XSS attacks
        SESSION_COOKIE_HTTPONLY=True
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
from services.text_generator import TextGenerator
from services.book_processor import BookProcessor
from models import TempBookData

text_service = TextGenerator()
book_processor = BookProcessor()

# Register blueprints
from blueprints.story import story_bp
from blueprints.generation import generation_bp

def initialize_app(app: Flask) -> None:
    """Initialize core application components and database.
    
    This function performs the following initialization steps:
    1. Initializes SQLAlchemy database connection
    2. Registers all blueprints for modular routing
    3. Creates database tables if they don't exist
    
    This should be called after configure_app() to ensure proper
    application setup sequence.
    
    Args:
        app (Flask): The Flask application instance to initialize
        
    Returns:
        None
        
    Raises:
        SQLAlchemyError: If database initialization fails
        ImportError: If required modules cannot be imported
    """
    db.init_app(app)
    app.register_blueprint(story_bp)
    app.register_blueprint(generation_bp)
    
    with app.app_context():
        import models
        db.create_all()

# Configure and initialize the application
configure_app(app)
initialize_app(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path: str) -> Union[Response, str]:
    """
    Main route handler for serving the React application.
    
    This function handles all non-API routes by serving the React frontend.
    It also manages session cleanup when returning to the home page.
    
    Args:
        path (str): The requested URL path
        
    Returns:
        Union[Response, str]: JSON response for API routes or rendered HTML template
    """
    # Clear any existing story data when returning to home
    if path == '' and 'story_data' in session:
        session.pop('story_data', None)
    
    # Only serve API routes, everything else goes to React
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
        
    return render_template('react.html')

@app.route('/generate_story', methods=['POST'])
def generate_story() -> Response:
    """
    Generate a new story based on user input parameters.
    
    This endpoint orchestrates the story generation process by:
    1. Validating required input parameters
    2. Generating story content using the text service
    3. Creating temporary storage for the story
    4. Setting up the user session for story editing
    
    Required Form Fields:
        - prompt (str): Main story prompt/theme
        - genre (str): Story genre category ('fantasy', 'mystery', etc.)
        - mood (str): Emotional tone/atmosphere
        - target_audience (str): Intended reader age group
        
    Optional Form Fields:
        - paragraphs (int): Number of paragraphs to generate (default: 5)
        
    Returns:
        Response: JSON containing:
            - success (bool): Operation status
            - redirect (str): URL to story editor on success
            - error (str): Error message if operation failed
            
    Raises:
        400: Missing or invalid required fields
        500: Story generation or database errors
        
    Example:
        >>> POST /generate_story
        >>> {
        >>>     "prompt": "A magical forest adventure",
        >>>     "genre": "fantasy",
        >>>     "mood": "whimsical",
        >>>     "target_audience": "young_adult"
        >>> }
        Returns: {
            "success": true,
            "redirect": "/story/edit"
        }
    """
    try:
        # Validate form data
        required_fields = ['prompt', 'genre', 'mood', 'target_audience']
        for field in required_fields:
            if not request.form.get(field):
                logger.error(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Extract and validate input parameters
        prompt = request.form.get('prompt')
        genre = request.form.get('genre')
        mood = request.form.get('mood')
        target_audience = request.form.get('target_audience')
        num_paragraphs = int(request.form.get('paragraphs', 5))
        
        # Log the start of story generation
        logger.info(f"Generating story with prompt: {prompt[:50]}...")
        
        # Generate story paragraphs using the text service
        story_paragraphs = text_service.generate_story(
            prompt=prompt,
            genre=genre,
            mood=mood,
            target_audience=target_audience,
            paragraphs=num_paragraphs  # Changed from num_paragraphs to match service
        )
            
        if not story_paragraphs:
            logger.error("Failed to generate story paragraphs")
            return jsonify({'error': 'Failed to generate story'}), 500
            
        # Create story data structure with metadata
        story_data = {
            'prompt': prompt,
            'genre': genre,
            'mood': mood,
            'target_audience': target_audience,
            'created_at': str(datetime.now()),
            'paragraphs': [
                {
                    'text': p,
                    'image_url': None,
                    'audio_url': None,
                    'image_style': 'realistic'
                } for p in story_paragraphs
            ]
        }
        
        # Persist story data in temporary storage
        try:
            temp_data = TempBookData(data=story_data)
            db.session.add(temp_data)
            db.session.commit()
            logger.info(f"Saved story data with temp_id: {temp_data.id}")
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error: {str(db_error)}")
            return jsonify({'error': 'Failed to save story data'}), 500
        
        # Update session with story data for user context
        session['story_data'] = {
            'temp_id': temp_data.id,
            'story_context': '\n\n'.join(story_paragraphs),
            'paragraphs': story_data['paragraphs']
        }
        session.modified = True
        
        logger.info("Story generation successful, redirecting to editor")
        return jsonify({
            'success': True,
            'redirect': '/story/edit'
        })
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error generating story: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    """
    Save the current story to persistent storage.
    
    Requires an active story session. The story data is retrieved from
    the session and saved to the database.
    
    Returns:
        Response: JSON response indicating success or failure
    """
    if 'story_data' not in session:
        return jsonify({'error': 'No story data found'}), 404
        
    try:
        # TODO: Implement story saving logic to database
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving story: {str(e)}")
        return jsonify({'error': str(e)}), 500

def log_error(error_code: int, message: str, exception: Exception = None, context: dict = None) -> None:
    """
    Centralized error logging function for consistent error tracking.
    
    This function provides standardized error logging across the application with
    configurable severity levels based on error codes. It includes additional
    context data and exception details when available.
    
    Args:
        error_code (int): HTTP error code determining severity level
        message (str): Primary error message to log
        exception (Exception, optional): Exception object for stack trace
        context (dict, optional): Additional contextual data for debugging
        
    Examples:
        >>> log_error(404, "User profile not found", context={'user_id': 123})
        >>> log_error(500, "Database connection failed", exception=db_error)
    
    Note:
        - 4xx errors are logged as warnings
        - 5xx errors are logged as errors
        - All errors include timestamp and request context
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'error_code': error_code,
        'message': message,
        'path': request.path,
        'method': request.method
    }
    
    if context:
        log_data['context'] = context
    if exception:
        log_data['exception'] = str(exception)
        log_data['exception_type'] = type(exception).__name__
        
    log_message = f"{error_code} error: {message}"
    if exception:
        log_message += f" - {type(exception).__name__}: {str(exception)}"
    
    if error_code >= 500:
        logger.error(log_message, extra=log_data)
    else:
        logger.warning(log_message, extra=log_data)

# Error Handlers
@app.errorhandler(404)
def not_found(e: Exception) -> tuple[Response, int]:
    """
    Handle 404 Not Found errors.
    
    Logs the attempt to access non-existent resources and returns a
    standardized JSON response. This handler ensures consistent error
    reporting across the application for missing resources.
    
    Args:
        e (Exception): The exception that triggered this handler
        
    Returns:
        tuple[Response, int]: JSON response with error details and 404 status
        
    Example:
        When accessing a non-existent route:
        >>> GET /invalid/route
        Returns: {"error": "The requested resource was not found"}, 404
    """
    log_error(404, f"Resource not found: {request.url}")
    return jsonify({
        'error': 'The requested resource was not found',
        'path': request.url,
        'status': 404
    }), 404

@app.errorhandler(500)
def server_error(e: Exception) -> tuple[Response, int]:
    """
    Handle 500 Internal Server errors.
    
    Logs the internal error details for debugging while returning a
    generic error message to the user for security.
    
    Args:
        e (Exception): The exception that triggered this handler
        
    Returns:
        tuple[Response, int]: JSON error response and 500 status code
    """
    log_error(500, "Internal server error", e)
    return jsonify({'error': 'An internal server error occurred'}), 500

@app.errorhandler(403)
def forbidden(e: Exception) -> Response:
    """
    Handle 403 Forbidden errors.
    
    Manages unauthorized access attempts by redirecting users to the home page
    with a friendly message explaining the required setup process.
    
    Args:
        e (Exception): The exception that triggered this handler
        
    Returns:
        Response: Redirect response to guide user to proper setup flow
        
    Note:
        Unlike other error handlers, this returns a redirect instead of JSON
        to maintain a smoother user experience for common setup-related issues.
    """
    log_error(403, f"Unauthorized access attempt: {request.url}")
    flash('Please start by creating a new story on the home page', 'warning')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(e: Exception) -> tuple[Response, int]:
    """
    Handle 413 Request Entity Too Large errors.
    
    Manages attempts to upload files that exceed the configured size limit,
    providing clear feedback about size restrictions.
    
    Args:
        e (Exception): The exception that triggered this handler
        
    Returns:
        tuple[Response, int]: JSON error response with size limit details
        
    Note:
        The response includes the actual size limit in MB to help users
        understand the constraint.
    """
    max_size_mb = MAX_CONTENT_LENGTH // (1024*1024)
    log_error(413, f"Upload exceeds {max_size_mb}MB limit")
    return jsonify({
        'error': f'File too large. Maximum size is {max_size_mb}MB.',
        'max_size_mb': max_size_mb
    }), 413

# Request Middleware
@app.before_request
def check_story_data() -> Optional[Response]:
    """
    Middleware to check for story data in session.
    
    Ensures that users have generated a story before accessing protected routes.
    Skips checks for static files and public routes.
    
    Returns:
        Optional[Response]: Redirect response if check fails, None otherwise
    """
    # Skip checks for public routes and static files
    excluded_paths = {
        '/static', 
        '/', 
        '/generate_story',
        '/story/upload'
    }
    
    if any(request.path.startswith(path) for path in excluded_paths):
        return None
        
    # Protect story-related routes
    protected_prefixes = ('/story/', '/save')
    if 'story_data' not in session and \
       any(request.path.startswith(prefix) for prefix in protected_prefixes):
        logger.warning(f"Unauthorized access attempt: {request.path}")
        flash('Please generate a story first', 'warning')
        return redirect(url_for('index'))
    
    return None

# React Application Routes
@app.route('/')
@app.route('/<path:path>')
def serve_react(path: str = '') -> str:
    """
    Universal handler for serving the React application.
    
    This is a catch-all handler that serves the main React application
    template for all frontend routes. It enables client-side routing
    to handle specific view rendering while maintaining a single backend
    entry point.
    
    Args:
        path (str, optional): The requested URL path. Defaults to empty string
            for root path requests.
    
    Returns:
        str: Rendered HTML template for the React application
        
    Note:
        This consolidates multiple separate route handlers into a single
        universal handler to reduce code redundancy and maintain a single
        source of truth for serving the React application.
    """
    # Clear session data when returning to home page
    if not path and 'story_data' in session:
        session.pop('story_data', None)
    
    return render_template('react.html')

@app.route('/api/story/data')
def get_story_data() -> Response:
    """
    Retrieve the current story data from the session.
    
    This endpoint provides access to the temporary story data
    stored in the session. It checks for valid session data
    and retrieves the corresponding temporary book data from
    the database.
    
    Returns:
        Response: JSON response containing story data or error message
        
    Status Codes:
        200: Successfully retrieved story data
        404: Story data not found in session or database
    """
    # Verify session data exists
    if 'story_data' not in session:
        logger.warning("Attempted to access story data with no session data")
        return jsonify({'error': 'No story data found'}), 404
        
    # Get temporary data ID from session
    temp_id = session['story_data'].get('temp_id')
    if not temp_id:
        logger.error("Session story data missing temp_id")
        return jsonify({'error': 'Invalid session data'}), 404
        
    # Retrieve temporary data from database
    temp_data = TempBookData.query.get(temp_id)
    if not temp_data:
        logger.error(f"Failed to find temporary data with ID: {temp_id}")
        return jsonify({'error': 'Story data not found'}), 404
        
    return jsonify({
        'success': True,
        'story': temp_data.data
    })

if __name__ == '__main__':
    # Run the Flask application
    port = int(os.environ.get('PORT', 80))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
