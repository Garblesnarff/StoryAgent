import os
from flask import Flask, render_template, request, session, jsonify, redirect, url_for, flash, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import secrets
from datetime import datetime
import json
import logging

from services.text_generator import TextGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = secrets.token_hex(16)  # Add secret key for session management
db.init_app(app)

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

def send_progress(agent, status, message):
    """Helper function to send progress updates"""
    logger.info(f"{agent}: {message}")
    return f"data: {json.dumps({'type': 'agent_progress', 'agent': agent, 'status': status, 'message': message})}\n\n"

@app.route('/')
def index():
    # Clear any existing story data when returning to home
    if 'story_data' in session:
        logger.info("Clearing existing story data from session")
        session.pop('story_data', None)
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    def generate():
        try:
            logger.info("Starting story generation process")
            
            # Validate form data
            required_fields = ['prompt', 'genre', 'mood', 'target_audience']
            for field in required_fields:
                if not request.form.get(field):
                    logger.error(f"Missing required field: {field}")
                    yield send_progress('Story Generation', 'error', f'Missing required field: {field}')
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Missing required field: {field}'})}\n\n"
                    return

            prompt = request.form.get('prompt')
            genre = request.form.get('genre')
            mood = request.form.get('mood')
            target_audience = request.form.get('target_audience')
            num_paragraphs = int(request.form.get('paragraphs', 5))

            logger.info(f"Generating story with parameters - Genre: {genre}, Mood: {mood}, Target Audience: {target_audience}")

            # Start Concept Generator
            yield send_progress('Concept Generator', 'active', 'Creating story concept...')
            concept = text_service.concept_generator.generate_concept(prompt, genre, mood, target_audience)
            if not concept:
                logger.error("Failed to generate concept")
                yield send_progress('Concept Generator', 'error', 'Failed to generate concept')
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate story concept'})}\n\n"
                return
            yield send_progress('Concept Generator', 'completed', 'Story concept created successfully')

            # Start World Builder
            yield send_progress('World Builder', 'active', 'Building story world...')
            world = text_service.world_builder.build_world(concept, genre, mood)
            if not world:
                logger.error("Failed to generate world")
                yield send_progress('World Builder', 'error', 'Failed to generate world')
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate world details'})}\n\n"
                return
            yield send_progress('World Builder', 'completed', 'Story world created successfully')

            # Start Plot Weaver
            yield send_progress('Plot Weaver', 'active', 'Developing plot structure...')
            plot = text_service.plot_weaver.weave_plot(concept, world, genre, mood)
            if not plot:
                logger.error("Failed to generate plot")
                yield send_progress('Plot Weaver', 'error', 'Failed to generate plot')
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate plot structure'})}\n\n"
                return
            yield send_progress('Plot Weaver', 'completed', 'Plot structure developed successfully')

            # Generate Story Text
            yield send_progress('Story Generator', 'active', 'Generating story text...')
            story_paragraphs = text_service.generate_story(prompt, genre, mood, target_audience, num_paragraphs)
            if not story_paragraphs:
                logger.error("Failed to generate story")
                yield send_progress('Story Generator', 'error', 'Failed to generate story')
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate story'})}\n\n"
                return

            # Store story data in session
            session['story_data'] = {
                'paragraphs': [{'text': p.strip()} for p in story_paragraphs if p.strip()]
            }
            session.modified = True
            session.permanent = True  # Make session data persistent

            # Send success response with redirect
            yield send_progress('Story Generator', 'completed', 'Story generated successfully')
            yield f"data: {json.dumps({'type': 'success', 'redirect': url_for('story.edit')})}\n\n"

        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            yield send_progress('Story Generation', 'error', str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to generate story'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/save_story', methods=['POST'])
def save_story():
    if 'story_data' not in session:
        logger.error("Attempted to save story without story data in session")
        return jsonify({'error': 'No story data found'}), 404
        
    try:
        # TODO: Implement story saving logic to database
        logger.info("Story saved successfully")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving story: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'The requested page was not found'}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({'error': 'An internal server error occurred'}), 500

@app.errorhandler(403)
def forbidden(e):
    logger.warning(f"403 error: {request.url}")
    return redirect(url_for('index'))

@app.before_request
def check_story_data():
    """Check if story data exists in session before accessing story-related routes"""
    # Skip check for static files and certain routes
    if request.path.startswith('/static') or request.path == '/' or request.path == '/generate_story':
        return
        
    # Redirect to index if trying to access story routes without story data
    if 'story_data' not in session and request.path.startswith('/story/'):
        flash('Please generate a story first')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=False)
