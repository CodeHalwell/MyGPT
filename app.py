import os
from flask import Flask, jsonify, g, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise
from security import csrf, limiter
from logging.handlers import RotatingFileHandler
from sqlalchemy import text
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import timedelta

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def get_db():
    if 'db' not in g:
        g.db = db
    return g.db

@app.teardown_appcontext
def teardown_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.session.remove()

def setup_logging(app):
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def init_db(app):
    """Initialize database with retry logic"""
    try:
        db.init_app(app)
        with app.app_context():
            db.engine.connect()
        logger.info("Database connection established successfully")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def create_app():
    app = Flask(__name__)
    
    # Configure static files
    app.static_folder = 'static'
    app.static_url_path = ''
    
    # Add WhiteNoise for serving static files
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=app.static_folder,
        prefix='',
        autorefresh=True,
        max_age=31536000
    )
    
    # Add ProxyFix middleware
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Security configurations
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Database configuration with connection pooling
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30
    }
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'codhe')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')

    # Initialize extensions with proper error handling
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
            # Create indexes if they don't exist
            with db.engine.connect() as conn:
                conn.execute(text('''
                    CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username);
                    CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email);
                    CREATE INDEX IF NOT EXISTS idx_message_chat_id ON message (chat_id);
                    CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat (user_id);
                '''))
                conn.commit()
        
        login_manager.init_app(app)
        csrf.init_app(app)
        limiter.init_app(app)
        login_manager.login_view = 'login'
        setup_logging(app)
        logger.info("Extensions initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing extensions: {str(e)}")
        raise

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error(f"Internal server error: {str(error)}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        db.session.rollback()
        logger.error(f"Unhandled exception: {str(e)}")
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({"error": "Forbidden"}), 403

    return app

app = create_app()
