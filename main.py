from app import app
import routes  # noqa: F401
import logging
from flask import g
from app import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
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

# The development server block is removed as we're using Gunicorn in production
