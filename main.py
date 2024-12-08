from app import app
import logging
import os
import psutil
import atexit
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup():
    """Cleanup function to ensure resources are properly released"""
    logger.info("Cleaning up server resources...")
    try:
        # Force close any sockets on our port
        kill_existing_process()
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def kill_existing_process():
    """Kill any process using the configured port"""
    try:
        port = Config.PORT
        for conn in psutil.net_connections():
            try:
                if hasattr(conn, 'laddr') and conn.laddr.port == port and conn.status == 'LISTEN':
                    try:
                        os.kill(conn.pid, 9)
                        logger.info(f"Killed process {conn.pid} using port {port}")
                    except (ProcessLookupError, PermissionError):
                        logger.warning(f"Could not kill process {conn.pid} using port {port}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
                continue
    except Exception as e:
        logger.error(f"Error checking for existing processes: {str(e)}")

def is_port_available(port):
    """Check if a port is available"""
    try:
        for conn in psutil.net_connections():
            if hasattr(conn, 'laddr') and conn.laddr.port == port:
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking port availability: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # Register cleanup function
        atexit.register(cleanup)
        
        # Kill any existing process using the port
        kill_existing_process()
        
        # Wait briefly for ports to be released
        import time
        time.sleep(1)
        
        # Verify port is available
        if not is_port_available(Config.PORT):
            logger.error(f"Port {Config.PORT} is still in use after cleanup attempt")
            raise OSError(f"Port {Config.PORT} is not available")
            
        logger.info(f"Starting Flask server on {Config.HOST}:{Config.PORT}...")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=True
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {Config.PORT} is already in use. Please ensure no other instance is running.")
        else:
            logger.error(f"Failed to start server: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error starting server: {str(e)}")
        raise
