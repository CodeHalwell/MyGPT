from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message
from chat_handler import get_ai_response

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
        
        user = User(
            username=request.form['username'],
            email=request.form['email']
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat.html', chats=chats)

@app.route('/chat/new', methods=['POST'])
@login_required
def new_chat():
    chat = Chat(user_id=current_user.id, title="New Chat")
    db.session.add(chat)
    db.session.commit()
    return jsonify({'chat_id': chat.id})

@app.route('/chat/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    content = request.json.get('message')
    user_message = Message(chat_id=chat_id, content=content, role='user')
    db.session.add(user_message)
    
    # Get chat history
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    
    # Get AI response
    ai_response = get_ai_response(messages)
    ai_message = Message(chat_id=chat_id, content=ai_response, role='assistant')
    db.session.add(ai_message)
    
    if not chat.title:
        chat.title = content[:30] + "..."
    
    db.session.commit()
    
    return jsonify({
        'user_message': content,
        'ai_response': ai_response
    })

@app.route('/chat/<int:chat_id>/messages')
@login_required
def get_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
    return jsonify([{
        'content': m.content,
        'role': m.role,
        'timestamp': m.timestamp.isoformat()
    } for m in messages])
