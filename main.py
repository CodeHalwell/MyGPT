import logging
import os
import traceback

from flask import g, request

import routes  # noqa: F401
from app import app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Ensure the database session is closed after each request."""
    db_session = getattr(g, "db_session", None)
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
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask production server on port {port}...")
        from waitress import serve

        serve(app, host="0.0.0.0", port=port, threads=6)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
