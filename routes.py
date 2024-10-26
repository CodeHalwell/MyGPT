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

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/settings/update', methods=['POST'])
@login_required
def update_settings():
    username = request.form.get('username')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect')
        return redirect(url_for('settings'))

    if username != current_user.username:
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('settings'))
        current_user.username = username

    if new_password:
        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('settings'))
        current_user.set_password(new_password)

    db.session.commit()
    flash('Settings updated successfully')
    return redirect(url_for('settings'))

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

# Rest of the existing routes...
