"""
WebSocket Connection Management for Hume AI
-----------------------------------------
This module handles WebSocket connections to the Hume AI API, including
connection initialization, management, and cleanup.
"""

import websockets
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class HumeWebSocketManager:
    """Manages WebSocket connections to the Hume AI API."""
    
    def __init__(self):
        """Initialize the WebSocket manager with API configuration."""
        self.base_url = "wss://api.hume.ai/v0/evi/chat"
        self._setup_connection_params()
        
    def _setup_connection_params(self):
        """Set up connection parameters using environment variables."""
        config_id = os.environ.get('HUME_CONFIG_ID')
        api_key = os.environ.get('HUME_API_KEY')
        
        params = [
            f"config_id={config_id}",
            "evi_version=2",
            f"api_key={api_key}"
        ]
        
        self.ws_url = f"{self.base_url}?{'&'.join(params)}"
        
    async def connect(self) -> Optional[Dict[str, Any]]:
        """
        Establish a WebSocket connection to the Hume AI API.
        
        Returns:
            Optional[Dict[str, Any]]: Connection metadata if successful, None otherwise
            
        Raises:
            websockets.exceptions.WebSocketException: If connection fails
        """
        try:
            self.ws = await websockets.connect(self.ws_url)
            metadata = await self.ws.recv()
            return json.loads(metadata)
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {str(e)}")
            raise
            
    async def send_message(self, message: Dict[str, Any]) -> None:
        """
        Send a message through the WebSocket connection.
        
        Args:
            message (Dict[str, Any]): The message to send
            
        Raises:
            websockets.exceptions.WebSocketException: If sending fails
        """
        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            raise
            
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Receive a message from the WebSocket connection.
        
        Returns:
            Optional[Dict[str, Any]]: Received message if successful, None otherwise
            
        Raises:
            websockets.exceptions.WebSocketException: If receiving fails
        """
        try:
            response = await self.ws.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to receive message: {str(e)}")
            raise
            
    async def close(self) -> None:
        """Close the WebSocket connection safely."""
        if hasattr(self, 'ws'):
            try:
                await self.ws.close()
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {str(e)}")
