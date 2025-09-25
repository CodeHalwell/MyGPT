"""
Base configuration settings for MyGPT application
"""
import os


class BaseConfig:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    REMEMBER_COOKIE_DURATION = 2592000  # 30 days
    
    # Admin settings
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'codhe')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'danielhalwell@gmail.com')
    
    # AI Provider settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
    
    # Email settings
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    VERIFIED_SENDER_EMAIL = os.environ.get('VERIFIED_SENDER_EMAIL')
    
    # Security settings
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_SSL_STRICT = False  # Allow HTTP for development
    
    # Static files
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year for static files


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///dev.db'
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "echo": True,  # Log all SQL queries in development
    }
    
    # Security (relaxed for development)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours for development
    WTF_CSRF_ENABLED = False  # Disable CSRF for development


class ProductionConfig(BaseConfig):
    """Production configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "echo": False,
    }
    
    # Security (strict for production)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_SSL_STRICT = True
    
    # Additional production settings
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(BaseConfig):
    """Testing configuration"""
    
    DEBUG = False
    TESTING = True
    
    # Database (in-memory SQLite for tests)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }
    
    # Security (disabled for testing)
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Email (disabled for testing)
    SENDGRID_API_KEY = None
    VERIFIED_SENDER_EMAIL = 'test@example.com'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}