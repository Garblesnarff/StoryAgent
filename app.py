"""
Flask App Module
---------------
This module provides the Flask application instance for use by other modules.
The actual server configuration and startup is handled by main.py.
"""

from main import create_app

# Create the Flask application instance
app = create_app()

# This file only provides the app instance for other modules to import
# Server startup and configuration is handled by main.py
if __name__ == '__main__':
    print("Please use 'python main.py' to start the server.")
    sys.exit(1)

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

# This file only contains Flask app configuration and routes
# Server startup is handled by main.py
if __name__ == '__main__':
    logger.error("Direct execution of app.py is not supported. Use main.py to start the server.")
    import sys
    sys.exit(1)
    
# Clear any existing server status
app.config['SERVER_START_TIME'] = None
