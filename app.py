import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise
from flask_talisman import Talisman

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

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
    
    # Configure ProxyFix for proper header handling behind Replit's proxy
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,      # Number of proxy servers
        x_proto=1,    # SSL termination happens at proxy
        x_host=1,     # Original host header
        x_port=1,     # Original port
        x_prefix=1    # Handle proxy path rewrites
    )
    
    # Security settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_DURATION'] = 3600  # 1 hour
    
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30
    }
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'codhe')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')

    # Initialize extensions
    try:
        db.init_app(app)
        login_manager.init_app(app)
        login_manager.login_view = 'login'
        logger.info("Database and login manager initialized successfully")
        
        # Initialize Talisman with security headers for Replit environment
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            session_cookie_secure=True,
            content_security_policy={
                'default-src': "'self'",
                'img-src': "'self' data:",
                'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com cdn.replit.com",
                'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com cdn.replit.com",
                'font-src': "'self' cdn.jsdelivr.net cdnjs.cloudflare.com",
                'connect-src': "'self' *"  # Updated to allow SSE connections
            },
            content_security_policy_nonce_in=['script-src'],
            force_file_save=True
        )
        
    except Exception as e:
        logger.error(f"Error initializing extensions: {str(e)}")
        raise

    with app.app_context():
        try:
            import models
            # Only create tables if they don't exist
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    return app

app = create_app()
