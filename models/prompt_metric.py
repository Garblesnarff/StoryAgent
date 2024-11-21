from datetime import datetime
from database import db

class PromptMetric(db.Model):
    __tablename__ = 'prompt_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    prompt_type = db.Column(db.String(50))
    generation_time = db.Column(db.Float)
    num_refinement_steps = db.Column(db.Integer)
    success = db.Column(db.Boolean)
    cache_hit = db.Column(db.Boolean)
    prompt_length = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    def __repr__(self):
        return f'<PromptMetric {self.id} {self.prompt_type}>'
