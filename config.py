import os

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a_secret_key'
    PORT = int(os.environ.get('PORT', 5001))  # Default to 5001 to avoid common conflicts
    HOST = '0.0.0.0'  # Allow external access
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # API Keys
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    TOGETHER_AI_API_KEY = os.environ.get('TOGETHER_AI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
