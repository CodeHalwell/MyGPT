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
    hue = random.randint(0, 360)
    saturation = random.randint(50, 90)
    lightness = random.randint(35, 65)
    
    def hsl_to_hex(h, s, l):
        h = h / 360
        s = s / 100
        l = l / 100
        
        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p
            
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
            
        return '#{:02x}{:02x}{:02x}'.format(
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )
    
    return hsl_to_hex(hue, saturation, lightness)

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
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User()
        user.username = request.form['username']
        user.email = request.form['email']
        user.set_password(request.form['password'])
        
        if (user.username == app.config['ADMIN_USERNAME'] and 
            user.email == app.config['ADMIN_EMAIL']):
            user.is_admin = True
            user.is_approved = True
        else:
            user.is_approved = False
        
        db.session.add(user)
        db.session.commit()
        
        if not user.is_admin:
            email_sent = send_registration_email(user.email, user.username)
            if not email_sent:
                flash('Registration successful but email notification could not be sent.')
            else:
                flash('Your registration is pending approval from an administrator. You will receive an email when your account is approved.')
            
            admin_notified = send_admin_notification_email(user.email, user.username)
            if not admin_notified:
                app.logger.error(f"Failed to send admin notification for new user registration: {user.username}")
        
        if user.is_approved:
            login_user(user)
            return redirect(url_for('index'))
        
        return render_template('pending_approval.html')
            
    return render_template('register.html')

[Rest of the existing routes.py content remains the same...]
