"""
Database Configuration Module

This module initializes the SQLAlchemy database instance with a custom base model.
It provides the foundation for all database models in the application.

Features:
- Custom declarative base model for SQLAlchemy
- Flask-SQLAlchemy integration
- Type-safe model declarations
- Session management

Usage:
    from database import db
    
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Custom declarative base class for SQLAlchemy models.
    
    This class serves as the base for all database models in the application,
    providing common functionality and metadata handling.
    """
    pass

# Initialize SQLAlchemy with custom model class
db = SQLAlchemy(model_class=Base)
