import os

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'a_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    TOGETHER_AI_API_KEY = os.environ.get('TOGETHER_AI_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
