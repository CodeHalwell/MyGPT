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

@app.route('/admin')
@login_required
def admin():
    """Admin dashboard route with proper authorization."""
    if not current_user.is_admin:
        flash('Access denied.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    pending_users = User.query.filter_by(is_approved=False).all()
    tags = Tag.query.all()
    
    # Prepare data for JavaScript
    serialized_users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_approved': user.is_approved
    } for user in users]
    
    serialized_pending_users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in pending_users]
    
    return render_template('admin.html',
                         users=users,
                         pending_users=pending_users,
                         tags=tags,
                         serialized_users=serialized_users,
                         serialized_pending_users=serialized_pending_users)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please fill in all fields.')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        if user and not user.is_account_locked():
            if user.check_password(password):
                if not user.is_approved:
                    flash('Your account is pending approval.')
                    return redirect(url_for('pending_approval'))
                login_user(user)
                return redirect(url_for('chat'))
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        email = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        
        if not validate_username(username):
            flash('Invalid username format.')
            return redirect(url_for('register'))
        
        if not validate_email(email):
            flash('Invalid email format.')
            return redirect(url_for('register'))
        
        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain both letters and numbers.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        user.is_admin = user.email == app.config['ADMIN_EMAIL']
        user.is_approved = user.is_admin
        
        db.session.add(user)
        db.session.commit()
        
        send_registration_email(user.email, user.username)
        if not user.is_admin:
            send_admin_notification_email(user.email, user.username)
        
        if user.is_approved:
            login_user(user)
            return redirect(url_for('chat'))
        return redirect(url_for('pending_approval'))
    
    return render_template('register.html')

@app.route('/chat')
@login_required
def chat():
    """Main chat interface."""
    if not current_user.is_approved:
        return redirect(url_for('pending_approval'))
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat.html', chats=chats)

@app.route('/chat/new', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def new_chat():
    """Create a new chat."""
    chat = Chat(user_id=current_user.id)
    db.session.add(chat)
    db.session.commit()
    return jsonify({'chat_id': chat.id})

@app.route('/chat/<int:chat_id>/messages')
@login_required
def get_messages(chat_id):
    """Get messages for a specific chat."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
    return jsonify([{
        'content': message.content,
        'role': message.role,
        'model': message.model
    } for message in messages])

@app.route('/chat/<int:chat_id>/message', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def save_message(chat_id):
    """Save a new message with security checks."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    content = sanitize_input(data['message'])
    model = data.get('model', 'gpt-4o')
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = Message(chat_id=chat.id, content=content, role='user', model=model)
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/chat/<int:chat_id>/message/stream')
@login_required
@limiter.limit("20 per minute")
def stream_response(chat_id):
    """Stream AI response with security checks."""
    chat = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first_or_404()
    model = request.args.get('model', 'gpt-4o')
    
    if model not in MODEL_MAPPING:
        return jsonify({'error': 'Invalid model'}), 400
    
    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp).all()
    message_list = [{'role': m.role, 'content': m.content} for m in messages]
    
    return Response(
        stream_with_context(get_ai_response_stream(message_list, model)),
        content_type='text/event-stream'
    )

@app.route('/logout')
@login_required
def logout():
    """Secure logout functionality."""
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET'])
@login_required
def settings():
    """User settings page."""
    return render_template('settings.html')

@app.route('/settings/username', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def update_username():
    """Update username with security checks."""
    new_username = sanitize_input(request.form.get('new_username', ''))
    current_password = request.form.get('current_password', '')
    
    if not validate_username(new_username):
        flash('Invalid username format.')
        return redirect(url_for('settings'))
    
    if not current_user.check_password(current_password):
        flash('Incorrect password.')
        return redirect(url_for('settings'))
    
    if User.query.filter_by(username=new_username).first():
        flash('Username already exists.')
        return redirect(url_for('settings'))
    
    current_user.username = new_username
    db.session.commit()
    flash('Username updated successfully.')
    return redirect(url_for('settings'))

@app.route('/settings/password', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def update_password():
    """Update password with security checks."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not current_user.check_password(current_password):
        flash('Incorrect current password.')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.')
        return redirect(url_for('settings'))
    
    if not validate_password(new_password):
        flash('Password must be at least 8 characters long and contain both letters and numbers.')
        return redirect(url_for('settings'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully.')
    return redirect(url_for('settings'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
