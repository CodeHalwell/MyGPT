from app import app
import routes  # noqa: F401
import logging
from flask import g
from app import db
import os

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Ensure the database session is closed after each request."""
    db_session = getattr(g, 'db_session', None)
    if db_session is not None:
        if exception:
            logger.error(f"Database error during request: {str(exception)}")
            db_session.rollback()
        db_session.close()

# For development server only
if __name__ == "__main__":
    try:
        # Use port 5000 as per flask_website blueprint
        port = int(os.environ.get('PORT', 5000))
        
        logger.info(f"Starting Flask development server on port {port}...")
        logger.info("External access enabled (0.0.0.0)")
        
        # Run the application with external access enabled
        app.run(
            host="0.0.0.0",  # Allow external access
            port=port,
            debug=True,      # Enable debug mode for development
            use_reloader=True  # Enable auto-reload on code changes
        )
    except OSError as e:
        logger.error(f"Port {port} is already in use. Please try a different port or stop any running server.")
        raise
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
