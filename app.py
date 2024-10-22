import eventlet
eventlet.monkey_patch()

import os
import traceback
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO
import groq
from config import Config

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

if not app.config['GROQ_API_KEY']:
    raise ValueError("GROQ_API_KEY is not set in the environment variables")

groq_client = groq.Client(api_key=app.config['GROQ_API_KEY'])

def log_message(message, progress=None):
    app.logger.info(message)
    socketio.emit('log_message', {'message': message, 'progress': progress})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_story', methods=['POST'])
def generate_story():
    prompt = request.form.get('prompt')
    
    try:
        with app.app_context():
            app.logger.debug('Starting story generation')
            log_message('Starting story generation process')
            log_message(f'Received prompt: {prompt[:50]}...')
            
            log_message("Calling Groq API to generate story")
            try:
                response = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {"role": "system", "content": "You are a creative storyteller. Write the first scene of the first chapter based on the given prompt."},
                        {"role": "user", "content": f"Write the first scene of a story based on this prompt: {prompt}"}
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )
                scene = response.choices[0].message.content
                app.logger.debug(f'Groq API response: {scene[:100]}...')  # Log first 100 characters
                log_message(f"Received response from Groq API. Generated {len(scene.split())} words.")
            except groq.error.APIError as e:
                app.logger.error(f"Groq API error: {str(e)}")
                log_message(f"Error calling Groq API: {str(e)}")
                return jsonify({'error': 'Failed to generate story', 'message': 'Error in story generation service'}), 500
            except Exception as e:
                app.logger.error(f"Unexpected error calling Groq API: {str(e)}")
                log_message(f"Unexpected error calling Groq API: {str(e)}")
                return jsonify({'error': 'Failed to generate story', 'message': 'An unexpected error occurred'}), 500

            log_message("Splitting scene into paragraphs")
            paragraphs = scene.split('\n\n')
            total_paragraphs = len(paragraphs)
            log_message(f"Split scene into {total_paragraphs} paragraphs")

            socketio.emit('total_paragraphs', {'total': total_paragraphs})

            for index, paragraph in enumerate(paragraphs):
                if paragraph.strip():
                    app.logger.debug(f'Processing paragraph {index + 1}')
                    log_message(f"Processing paragraph {index + 1} of {total_paragraphs}. First few words: {' '.join(paragraph.split()[:5])}...", progress={'current': index + 1, 'total': total_paragraphs})
                    
                    log_message(f"Generating image for paragraph {index + 1}", progress={'current': index + 1, 'total': total_paragraphs})
                    image_url = generate_image_for_paragraph(paragraph)
                    if image_url:
                        app.logger.debug(f'Generated image URL: {image_url[:50]}...')
                        log_message(f"Image generated for paragraph {index + 1}. URL: {image_url[:50]}...", progress={'current': index + 1, 'total': total_paragraphs})
                    else:
                        log_message(f"Failed to generate image for paragraph {index + 1}. Using fallback image.", progress={'current': index + 1, 'total': total_paragraphs})
                        image_url = 'https://example.com/fallback-image.jpg'
                    
                    log_message(f"Generating audio for paragraph {index + 1}", progress={'current': index + 1, 'total': total_paragraphs})
                    audio_url = generate_audio_for_paragraph(paragraph)
                    if audio_url:
                        app.logger.debug(f'Generated audio URL: {audio_url}')
                        log_message(f"Audio generated for paragraph {index + 1}. File: {os.path.basename(audio_url)}", progress={'current': index + 1, 'total': total_paragraphs})
                    else:
                        log_message(f"Failed to generate audio for paragraph {index + 1}. Skipping audio.", progress={'current': index + 1, 'total': total_paragraphs})
                    
                    socketio.emit('new_paragraph', {
                        'text': paragraph,
                        'image_url': image_url,
                        'audio_url': audio_url or ''
                    })

            app.logger.debug('Story generation complete')
            log_message(f"Story generation process complete. Processed {total_paragraphs} paragraphs.")
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error generating story: {str(e)}")
        app.logger.error(traceback.format_exc())
        log_message(f"Error generating story: {str(e)}")
        return jsonify({'error': 'Failed to generate story', 'message': 'An unexpected error occurred'}), 500

@app.route('/save_story', methods=['POST'])
def save_story():
    # TODO: Implement story saving logic using Supabase
    return jsonify({'success': True})

def generate_image_for_paragraph(paragraph):
    # TODO: Implement image generation logic
    return None

def generate_audio_for_paragraph(paragraph):
    # TODO: Implement audio generation logic
    return None

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
