import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import secrets

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('config.Config')
    app.config['SECRET_KEY'] = secrets.token_hex(16)
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    with app.app_context():
        # Import models and create tables
        import models
        db.create_all()
        
        # Register blueprints
        from blueprints.main import main as main_blueprint
        from blueprints.story import story as story_blueprint
        
        app.register_blueprint(main_blueprint)
        app.register_blueprint(story_blueprint, url_prefix='/story')
        
        return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
