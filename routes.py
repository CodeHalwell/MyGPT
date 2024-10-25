from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message
from chat_handler import get_ai_response_stream, generate_chat_summary

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
        
        user = User()
        user.username = request.form['username']
        user.email = request.form['email']
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
    chat = Chat()
    chat.user_id = current_user.id
    chat.title = "New Chat"
    db.session.add(chat)
    db.session.commit()
    return jsonify({'chat_id': chat.id})

@app.route('/chat/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 415
    
    content = request.json.get('message')
    if not content:
        return jsonify({'error': 'Message content is required'}), 400

    user_message = Message()
    user_message.chat_id = chat_id
    user_message.content = content
    user_message.role = 'user'
    db.session.add(user_message)
    db.session.flush()

    def generate():
        try:
            # Send SSE headers
            yield 'event: message\n'
            
            messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            accumulated_response = []
            
            for chunk in get_ai_response_stream(messages):
                accumulated_response.append(chunk)
                yield f"data: {chunk}\n\n"
            
            complete_response = ''.join(accumulated_response)
            ai_message = Message()
            ai_message.chat_id = chat_id
            ai_message.content = complete_response
            ai_message.role = 'assistant'
            db.session.add(ai_message)
            
            # Generate and update chat summary
            all_messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            chat.title = generate_chat_summary(all_messages)
            db.session.commit()
            
            yield 'data: [DONE]\n\n'
        except Exception as e:
            db.session.rollback()
            yield f'data: error: {str(e)}\n\n'
            yield 'data: [DONE]\n\n'

    response = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )
    return response

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

@app.route('/chat/<int:chat_id>/title', methods=['GET'])
@login_required
def get_chat_title(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'title': chat.title})
