import logging
import os
import psutil
import atexit
import time
import socket
from app import app
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup():
    """Cleanup function to ensure resources are properly released"""
    logger.info("Cleaning up server resources...")
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        return
        
    try:
        kill_existing_process()
        time.sleep(0.5)  # Short delay to ensure cleanup completes
        
        # Double check if port is actually free
        if not is_port_available(Config.PORT):
            logger.warning(f"Port {Config.PORT} still in use after cleanup")
            kill_existing_process()  # Try one more time
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
    finally:
        logger.info("Cleanup process completed")

def kill_existing_process():
    """Kill any process using the configured port"""
    try:
        port = Config.PORT
        current_pid = os.getpid()
        
        for conn in psutil.net_connections():
            try:
                if (hasattr(conn, 'laddr') and 
                    conn.laddr.port == port and 
                    conn.status == 'LISTEN' and 
                    conn.pid != current_pid):  # Don't kill ourselves
                    
                    try:
                        proc = psutil.Process(conn.pid)
                        # Try graceful termination first
                        proc.terminate()
                        logger.info(f"Attempting to terminate process {conn.pid} using port {port}")
                        
                        # Wait for process to terminate
                        try:
                            proc.wait(timeout=3)
                            logger.info(f"Successfully terminated process {conn.pid}")
                        except psutil.TimeoutExpired:
                            # If graceful termination fails, force kill
                            logger.warning(f"Process {conn.pid} didn't terminate gracefully, forcing kill")
                            proc.kill()
                            proc.wait(timeout=1)
                            logger.info(f"Forcefully killed process {conn.pid}")
                            
                    except (ProcessLookupError, PermissionError, psutil.NoSuchProcess):
                        logger.warning(f"Process {conn.pid} no longer exists or permission denied")
                    except Exception as kill_error:
                        logger.error(f"Error killing process {conn.pid}: {str(kill_error)}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error) as e:
                logger.debug(f"Error accessing process: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"Error checking for existing processes: {str(e)}")

def is_port_available(port):
    """Check if a port is available"""
    sock = None
    try:
        # Create socket with address reuse
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Try to bind to the port
        sock.bind(('0.0.0.0', port))
        sock.listen(1)
        sock.close()
        return True
        
    except socket.error as e:
        logger.warning(f"Port {port} is not available: {str(e)}")
        return False
        
    finally:
        if sock:
            try:
                sock.close()
            except socket.error:
                pass

if __name__ == "__main__":
    try:
        # Only perform cleanup and port checks in the main process
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            # Register cleanup handler
            atexit.register(cleanup)
            
            # Initial cleanup
            logger.info("Performing initial cleanup...")
            kill_existing_process()
            time.sleep(1)  # Brief delay for cleanup
            
            # Verify port availability with retries
            max_retries = 3
            retry_count = 0
            while not is_port_available(Config.PORT):
                if retry_count >= max_retries:
                    logger.error(f"Port {Config.PORT} is still in use after {max_retries} cleanup attempts")
                    raise OSError(f"Port {Config.PORT} is not available")
                    
                logger.warning(f"Port {Config.PORT} still in use, retry {retry_count + 1}/{max_retries}")
                kill_existing_process()
                retry_count += 1
                time.sleep(2)  # Increasing delay between retries
                
            logger.info(f"Port {Config.PORT} is available, proceeding with server startup")
            
        # Configure server
        logger.info(f"Starting Flask server on {Config.HOST}:{Config.PORT}...")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            use_reloader=False,  # Disable reloader for stability
            threaded=True,
            use_debugger=False  # Disable debugger in production
        )
        
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {Config.PORT} is already in use. Please ensure no other instance is running.")
        else:
            logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error starting server: {str(e)}")
        sys.exit(1)
