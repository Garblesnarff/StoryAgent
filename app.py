"""
Flask App Module
---------------
Primary application factory and configuration module.
"""

import os
import logging
import secrets
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash
from flask_cors import CORS
from database import db
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = secrets.token_hex(16)
    
    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Initialize database
    db.init_app(app)
    with app.app_context():
        db.create_all()
        logger.info("Database initialized successfully")
        
    # Register blueprints
    with app.app_context():
        from blueprints.story import story_bp
        from blueprints.generation import generation_bp
        app.register_blueprint(story_bp)
        app.register_blueprint(generation_bp)
    
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
    
    return app

# Create the Flask application instance
app = create_app()