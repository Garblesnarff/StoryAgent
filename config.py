import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    TOGETHER_AI_API_KEY = os.environ.get('TOGETHER_AI_API_KEY')
    HUME_API_KEY = os.environ.get('HUME_API_KEY')
    HUME_SECRET_KEY = os.environ.get('HUME_SECRET_KEY')
    HUME_CONFIG_ID = 'default'  # Update with actual config ID if needed
