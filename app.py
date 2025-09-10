import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure static files with absolute path
    app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.static_url_path = '/static'
    
    # Configure WhiteNoise for production static file serving
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=app.static_folder,
        prefix=app.static_url_path,
        autorefresh=False,  # Disable autorefresh in production
        max_age=31536000,  # Cache for 1 year
        index_file=False
    )
    
    # Add ProxyFix middleware for proper header handling behind Replit's proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Production configurations
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
    database_url = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    
    # Configure engine options based on database type
    if database_url and 'sqlite' in database_url:
        # SQLite configuration
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
        }
    else:
        # PostgreSQL configuration
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30
        }
    
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'codhe')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')
    
    # Production security settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['REMEMBER_COOKIE_DURATION'] = 2592000  # 30 days
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

    # Initialize extensions
    try:
        db.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = 'login'
        logger.info("Database and login manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing extensions: {str(e)}")
        raise

    with app.app_context():
        try:
            import models
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    return app

app = create_app()
