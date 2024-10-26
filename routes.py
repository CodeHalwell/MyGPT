import random
from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from markupsafe import escape
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, limiter, csrf
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags, MODEL_MAPPING
from email_handler import (
    send_registration_email, send_approval_email, send_admin_notification_email,
    send_password_reset_email
)
import secrets
from datetime import datetime, timedelta
import re
import bleach
from werkzeug.security import generate_password_hash
from sqlalchemy import text

def sanitize_input(content):
    """Sanitize user input using bleach."""
    allowed_tags = ['b', 'i', 'u', 'p', 'code', 'pre', 'br']
    return bleach.clean(content, tags=allowed_tags, strip=True)

def validate_username(username):
    """Validate username format."""
    if not username or len(username) < 3 or len(username) > 64:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

def validate_email(email):
    """Validate email format."""
    if not email or len(email) > 120:
        return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def validate_password(password):
    """Validate password strength."""
    if not password or len(password) < 8:
        return False
    return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', password))

@app.before_request
def before_request():
    """Security checks before each request."""
    if not request.is_secure and not app.debug:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

@app.route('/')
def index():
    """Secure root route with proper redirection."""
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    """Main chat interface route."""
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat.html', chats=chats)

@app.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Handle forgot password requests."""
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', ''))
        if not validate_email(email):
            flash('Invalid email format.')
            return redirect(url_for('forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            send_password_reset_email(user.email, user.username, token)
            flash('If an account exists with that email, a password reset link has been sent.')
        else:
            # Still show success message to prevent email enumeration
            flash('If an account exists with that email, a password reset link has been sent.')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def reset_password(token):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired reset link.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain both letters and numbers.')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been updated. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')
