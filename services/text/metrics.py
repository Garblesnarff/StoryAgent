"""
Metrics Recording Module
----------------------
This module handles recording and tracking of text generation metrics.
It integrates with the database to store performance data and error information.
"""

import logging
from datetime import datetime
from database import db
from models import PromptMetric

logger = logging.getLogger(__name__)

class MetricsRecorder:
    """Handles recording of text generation metrics."""
    
    def record(self, prompt_type, generation_time, success, prompt_length=0, error_msg=None):
        """
        Record prompt generation metrics.
        
        Args:
            prompt_type (str): Type of prompt generation
            generation_time (float): Time taken for generation
            success (bool): Whether generation was successful
            prompt_length (int): Length of the input prompt
            error_msg (str, optional): Error message if generation failed
        """
        try:
            metric = PromptMetric(
                prompt_type=prompt_type,
                generation_time=generation_time,
                num_refinement_steps=1,  # Text generation is single-step
                success=success,
                prompt_length=prompt_length,
                error_message=error_msg
            )
            db.session.add(metric)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error recording metrics: {str(e)}")
            db.session.rollback()
