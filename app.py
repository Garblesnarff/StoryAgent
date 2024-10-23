import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
import urllib.parse
from config import Config
import groq
from together import Together
import time
import tempfile
from collections import deque
from datetime import datetime, timedelta
import json
import sys
import base64
import asyncio
from dotenv import load_dotenv
from hume import AsyncHumeClient
from hume.empathic_voice.chat.socket_client import ChatConnectOptions, ChatWebsocketConnection
from hume.empathic_voice.chat.types import SubscribeEvent, MessageEvent, AudioEvent
from hume.empathic_voice.types import AudioOutput

# Load environment variables
load_dotenv()

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Initialize API clients
groq_client = groq.Groq(api_key=app.config['GROQ_API_KEY'])
together_client = Together(api_key=os.environ.get('TOGETHER_AI_API_KEY'))
hume_client = AsyncHumeClient(api_key=os.environ.get('HUME_API_KEY'))

# Rate limiting for image generation
image_generation_queue = deque(maxlen=6)
IMAGE_RATE_LIMIT = 60  # 60 seconds (1 minute)

class WebSocketInterface:
    def __init__(self):
        self.socket = None
        self.audio_data = None
        self.is_connected = False
        self.error = None
        self.received_messages = []
        
    def set_socket(self, socket: ChatWebsocketConnection):
        self.socket = socket
        
    async def on_open(self):
        app.logger.info("WebSocket connection opened")
        self.is_connected = True
        self.error = None
        
    async def on_message(self, data: SubscribeEvent):
        try:
            app.logger.info(f"Received message: {type(data)}")
            self.received_messages.append(data)
            
            if isinstance(data, AudioEvent):
                # Extract audio data from the audio event
                self.audio_data = data.audio
                app.logger.info("Received audio data from AudioEvent")
            elif isinstance(data, AudioOutput):
                # Handle legacy AudioOutput type
                self.audio_data = getattr(data, 'audio', None)
                app.logger.info("Received audio data from AudioOutput")
            elif isinstance(data, MessageEvent):
                app.logger.info(f"Received message event: {data.message}")
                
        except Exception as e:
            app.logger.error(f"Error processing message: {str(e)}")
            self.error = str(e)
            
    async def on_close(self):
        app.logger.info("WebSocket connection closed")
        self.is_connected = False
        
    async def on_error(self, error: Exception):
        app.logger.error(f"WebSocket error: {str(error)}")
        self.error = str(error)
        self.is_connected = False

async def generate_audio_with_evi(text):
    try:
        app.logger.info(f"Generating audio for text: {text[:50]}...")
        
        # Initialize WebSocket interface
        websocket_interface = WebSocketInterface()
        
        # Setup EVI connection options with proper configuration
        options = ChatConnectOptions(
            config_id=os.environ.get('HUME_CONFIG_ID'),
            secret_key=os.environ.get('HUME_SECRET_KEY')
        )
        
        # Connect to EVI with proper error handling
        try:
            async with hume_client.empathic_voice.chat.connect_with_callbacks(
                options=options,
                on_open=websocket_interface.on_open,
                on_message=websocket_interface.on_message,
                on_close=websocket_interface.on_close,
                on_error=websocket_interface.on_error
            ) as socket:
                websocket_interface.set_socket(socket)
                
                # Wait for connection to be established
                start_time = time.time()
                while not websocket_interface.is_connected and (time.time() - start_time) < 10:
                    if websocket_interface.error:
                        raise Exception(f"Connection error: {websocket_interface.error}")
                    await asyncio.sleep(0.1)
                
                if not websocket_interface.is_connected:
                    raise Exception("Failed to establish WebSocket connection")
                
                # Send text to be converted to speech
                await socket.empathic_voice.send_text(text)
                app.logger.info("Sent text message")
                
                # Wait for audio response (with timeout)
                start_time = time.time()
                while not websocket_interface.audio_data:
                    if websocket_interface.error:
                        raise Exception(f"WebSocket error: {websocket_interface.error}")
                    if (time.time() - start_time) > 30:
                        raise Exception("Timeout waiting for audio response")
                    await asyncio.sleep(0.1)
                
                if not websocket_interface.audio_data:
                    raise Exception("No audio data received")
                
                # Save audio to file
                audio_dir = os.path.join('static', 'audio')
                os.makedirs(audio_dir, exist_ok=True)
                
                filename = f"paragraph_audio_{int(time.time())}.mp3"
                filepath = os.path.join(audio_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(websocket_interface.audio_data)
                
                return f"/static/audio/{filename}"
                
        except Exception as ws_error:
            raise Exception(f"WebSocket connection error: {str(ws_error)}")
            
    except Exception as e:
        app.logger.error(f"Error generating audio: {str(e)}")
        return None

[Rest of the file content remains unchanged...]
