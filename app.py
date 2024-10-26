import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from whitenoise import WhiteNoise

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
    
    # Add ProxyFix middleware
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
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
