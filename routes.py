from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags

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
            if not user.is_approved and not user.is_admin:
                flash('Your account is pending approval from an administrator.')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

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
        
        # Only the first user becomes admin and gets auto-approved
        is_first_user = User.query.count() == 0
        if is_first_user:
            user.is_admin = True
            user.is_approved = True
        
        db.session.add(user)
        db.session.commit()
        
        # Only log in and redirect to index if user is the first admin
        if is_first_user:
            login_user(user)
            return redirect(url_for('index'))
            
        # All other users go to pending approval page
        return redirect(url_for('pending_approval'))
            
    return render_template('register.html')

@app.route('/pending-approval')
def pending_approval():
    return render_template('pending_approval.html')

[Rest of the routes.py file content remains unchanged...]
