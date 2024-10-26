from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
import logging

csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

# Input validation constants
MAX_USERNAME_LENGTH = 64
MAX_EMAIL_LENGTH = 120
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_username(username):
    if not username or len(username) > MAX_USERNAME_LENGTH:
        return False, "Username must be between 1 and 64 characters."
    if not username.replace('_', '').replace('-', '').isalnum():
        return False, "Username can only contain letters, numbers, underscores, and hyphens."
    return True, None

def validate_email(email):
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return False, "Email must be between 1 and 120 characters."
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format."
    return True, None

def validate_password(password):
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be less than {MAX_PASSWORD_LENGTH} characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number."
    return True, None

def sanitize_input(text):
    if text is None:
        return ""
    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Convert special characters to HTML entities
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#x27;')
    return text
