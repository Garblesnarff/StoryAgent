from app import app
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
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
