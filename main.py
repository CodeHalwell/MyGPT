from app import app
import routes  # noqa: F401
import logging
from flask import g, jsonify
from app import db
from werkzeug.exceptions import HTTPException
import sys
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions."""
    # Log the full stack trace
    exc_info = sys.exc_info()
    logger.error("".join(traceback.format_exception(*exc_info)))
    
    # Handle HTTP exceptions
    if isinstance(e, HTTPException):
        response = e.get_response()
        response.data = jsonify({
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }).data
        response.content_type = "application/json"
        return response
    
    # Handle other exceptions
    return jsonify({
        "error": "Internal Server Error",
        "description": "An unexpected error occurred"
    }), 500

@app.after_request
def after_request(response):
    """Add security headers to every response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# For development server only
if __name__ == "__main__":
    try:
        logger.info("Starting Flask development server...")
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise
