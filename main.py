from app import app
import routes  # noqa: F401
import logging
from flask import g, request
from app import db
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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

@app.before_request
def before_request():
    """Log incoming requests."""
    logger.info(f"Incoming {request.method} request to {request.path}")

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Page not found: {request.path}")
    return "Page not found", 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    logger.error(traceback.format_exc())
    db.session.rollback()
    return "Internal server error", 500

# For production server
if __name__ == "__main__":
    try:
        logger.info("Starting Flask production server...")
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
