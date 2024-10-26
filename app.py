import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

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
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Security configurations
    app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30
    }
    app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', 'codhe')
    app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')
    
    # Security headers and cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['WTF_CSRF_SSL_STRICT'] = True
    
    # Initialize extensions
    try:
        db.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)
        limiter.init_app(app)
        login_manager.login_view = 'login'
        
        # Configure CORS
        CORS(app, 
             resources={
                 r"/*": {
                     "origins": [
                         f"https://{os.environ.get('REPL_SLUG', '')}.{os.environ.get('REPL_OWNER', '')}.repl.co",
                         "http://localhost:5000"
                     ],
                     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                     "allow_headers": ["Content-Type", "X-CSRF-Token"],
                     "expose_headers": ["Content-Range", "X-Content-Range"],
                     "supports_credentials": True,
                     "max_age": 600
                 }
             })
        
        # Configure Talisman
        csp = {
            'default-src': "'self'",
            'img-src': ["'self'", 'data:', 'https:'],
            'script-src': [
                "'self'",
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com',
                "'unsafe-inline'"  # Only for Bootstrap and specific dynamic content
            ],
            'style-src': [
                "'self'",
                'https://cdn.replit.com',
                'https://cdn.jsdelivr.net',
                'https://cdnjs.cloudflare.com',
                "'unsafe-inline'"  # Required for Bootstrap
            ],
            'font-src': ["'self'", 'https:', 'data:'],
            'connect-src': ["'self'", "https:"],
            'frame-ancestors': ["'none'"],
            'form-action': ["'self'"],
            'base-uri': ["'self'"],
            'manifest-src': ["'self'"]
        }
        
        Talisman(
            app,
            content_security_policy=csp,
            force_https=False,  # Since Replit handles HTTPS
            session_cookie_secure=True,
            feature_policy={
                'geolocation': "'none'",
                'microphone': "'none'",
                'camera': "'none'",
                'payment': "'none'",
                'usb': "'none'"
            },
            permissions_policy={
                'geolocation': '()',
                'microphone': '()',
                'camera': '()',
                'payment': '()',
                'usb': '()'
            }
        )
        
        logger.info("Security extensions initialized successfully")
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
