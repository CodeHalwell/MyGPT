from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from functools import wraps
from flask import request, abort
import re
import html

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Add specific rate limits for sensitive endpoints
login_limit = ["5 per minute", "100 per day"]
register_limit = ["3 per hour", "10 per day"]
password_reset_limit = ["3 per hour", "10 per day"]
api_limit = ["30 per minute", "1000 per day"]

# Secure headers configuration
talisman = Talisman(
    force_https=False,  # Set to True in production
    session_cookie_secure=True,
    content_security_policy={
        'default-src': ["'self'"],
        'img-src': ["'self'", "data:", "https:", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'script-src-elem': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.replit.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'style-src-elem': ["'self'", "'unsafe-inline'", "cdn.replit.com", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'font-src': ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'connect-src': ["'self'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'frame-ancestors': ["'none'"],
        'form-action': ["'self'"],
        'base-uri': ["'self'"],
        'object-src': ["'none'"],
        'upgrade-insecure-requests': [],
        'block-all-mixed-content': []
    },
    feature_policy={
        'geolocation': "'none'",
        'microphone': "'none'",
        'camera': "'none'",
        'payment': "'none'",
        'usb': "'none'",
        'accelerometer': "'none'",
        'autoplay': "'none'",
        'document-domain': "'none'",
        'encrypted-media': "'none'",
        'fullscreen': "'self'",
        'vibrate': "'none'",
        'magnetometer': "'none'",
        'midi': "'none'",
        'picture-in-picture': "'none'",
        'sync-xhr': "'self'",
        'browsing-topics': "'none'"
    },
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    strict_transport_security_include_subdomains=True,
    referrer_policy='same-origin'
)

def sanitize_input(text):
    """Sanitize user input to prevent XSS and injection attacks."""
    if not isinstance(text, str):
        return text
    
    # Remove potentially dangerous HTML tags and attributes
    text = re.sub(r'<[^>]*?>', '', text)
    # Escape special characters
    text = html.escape(text, quote=True)
    # Remove any potential JavaScript event handlers
    text = re.sub(r'on\w+\s*=', '', text)
    # Remove any potential JavaScript URLs
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    # Remove any potential data URLs
    text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
    return text

def validate_json_request(required_fields):
    """Decorator to validate JSON request data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                abort(400, description="Request must be JSON")
            data = request.get_json()
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                abort(400, description=f"Missing required fields: {', '.join(missing_fields)}")
            
            # Sanitize all string values in the request
            for field, value in data.items():
                if isinstance(value, str):
                    data[field] = sanitize_input(value)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator to ensure user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403, description="Admin access required")
        return f(*args, **kwargs)
    return decorated_function

def validate_password_strength(password):
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    return True, "Password meets strength requirements"
