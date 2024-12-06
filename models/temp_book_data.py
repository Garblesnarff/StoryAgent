from database import db
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class TempBookData(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, data: Dict[str, Any], id: Optional[str] = None, created_at: Optional[datetime] = None) -> None:
        if id is not None:
            self.id = id
        if created_at is not None:
            self.created_at = created_at
        self.data = data