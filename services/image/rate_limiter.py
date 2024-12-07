"""
Rate Limiting Module
-----------------
This module handles rate limiting for image generation requests to prevent API overload.
It manages request timing and enforces waiting periods between requests.
"""

from datetime import datetime, timedelta
from collections import deque
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Handles rate limiting for image generation requests."""
    
    def __init__(self):
        """Initialize rate limiter settings."""
        self.generation_queue = deque(maxlen=6)
        self.RATE_LIMIT = 60  # 60 seconds (1 minute)
        self.STEP_DELAY = 2  # 2 seconds between chain steps
        
    def check_and_wait(self):
        """
        Check rate limits and wait if necessary.
        
        This method ensures we don't exceed API rate limits by:
        1. Removing expired timestamps from the queue
        2. Waiting if we've hit the rate limit
        """
        current_time = datetime.now()
        
        # Remove expired timestamps
        while (self.generation_queue and 
               current_time - self.generation_queue[0] > timedelta(seconds=self.RATE_LIMIT)):
            self.generation_queue.popleft()
        
        # Wait if at rate limit
        if len(self.generation_queue) >= 6:
            wait_time = (
                self.generation_queue[0] + 
                timedelta(seconds=self.RATE_LIMIT) - 
                current_time
            ).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
                
    def record_generation(self):
        """Record a successful generation in the queue."""
        self.generation_queue.append(datetime.now())
        
    def wait_between_steps(self):
        """Wait between chain generation steps."""
        time.sleep(self.STEP_DELAY)
