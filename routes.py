from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, logger
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags
from email_handler import (
    send_registration_email, send_approval_email, send_admin_notification_email,
    send_password_reset_email
)
from security import (
    limiter, validate_username, validate_email, validate_password,
    sanitize_input, csrf
)
import secrets
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

@app.before_request
def before_request():
    if current_user.is_authenticated:
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)

def handle_db_error(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error in {f.__name__}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Database error occurred'}), 500
            flash('An error occurred while processing your request.')
            return redirect(url_for('index'))
    return decorated_function

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    try:
        # Clear any existing session data
        session.clear()
        logout_user()
        flash('You have been logged out successfully.')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return redirect(url_for('login'))

# ... rest of the routes.py content remains the same ...
