import random
from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags, MODEL_MAPPING
from email_handler import (
    send_registration_email, send_approval_email, send_admin_notification_email,
    send_password_reset_email
)
import secrets
from datetime import datetime, timedelta

def generate_random_color():
    # ... (keep existing function)
    pass

@app.route('/')
@login_required
def index():
    return redirect(url_for('chat'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            if not user.is_approved:
                flash('Your account is pending approval from an administrator.')
                return render_template('pending_approval.html')
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        # Auto-approve if this is the first user (admin)
        if User.query.count() == 0:
            user.is_approved = True
            user.is_admin = True
        
        db.session.add(user)
        try:
            db.session.commit()
            send_registration_email(user.email, user.username)
            if not user.is_approved:
                send_admin_notification_email(user.email, user.username)
                return redirect(url_for('pending_approval'))
            login_user(user)
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
            flash('Error during registration')
            return redirect(url_for('register'))
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/settings/update-username', methods=['POST'])
@login_required
def update_username():
    new_username = request.form.get('new_username')
    password_confirm = request.form.get('password_confirm')
    
    if not new_username or not password_confirm:
        flash('All fields are required.')
        return redirect(url_for('settings'))
    
    if not current_user.check_password(password_confirm):
        flash('Current password is incorrect.')
        return redirect(url_for('settings'))
    
    # Check if username is taken
    existing_user = User.query.filter_by(username=new_username).first()
    if existing_user and existing_user.id != current_user.id:
        flash('Username is already taken.')
        return redirect(url_for('settings'))
    
    # Update username
    current_user.username = new_username
    db.session.commit()
    flash('Username updated successfully.')
    return redirect(url_for('settings'))

@app.route('/settings/update-password', methods=['POST'])
@login_required
def update_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([current_password, new_password, confirm_password]):
        flash('All fields are required.')
        return redirect(url_for('settings'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.')
        return redirect(url_for('settings'))
    
    if current_password == new_password:
        flash('New password must be different from current password.')
        return redirect(url_for('settings'))
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    flash('Password updated successfully.')
    return redirect(url_for('settings'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            if send_password_reset_email(user.email, user.username, token):
                flash('Password reset instructions have been sent to your email.')
            else:
                flash('Error sending password reset email. Please try again later.')
        else:
            # Always show the same message to prevent email enumeration
            flash('If an account exists with this email, you will receive password reset instructions.')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        flash('Invalid or expired password reset link.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Your password has been updated. You can now log in with your new password.')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/pending_approval')
def pending_approval():
    return render_template('pending_approval.html')

# Rest of the routes...
