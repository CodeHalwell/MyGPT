from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags
from email_handler import send_registration_email, send_approval_email

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
        
        if user.is_approved:
            login_user(user)
            return redirect(url_for('index'))
        
        return render_template('pending_approval.html')
            
    return render_template('register.html')

@app.route('/pending-approval')
def pending_approval():
    return render_template('pending_approval.html')

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('You have been logged out.')
        return redirect(url_for('login'))
    except Exception as e:
        app.logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout.')
        return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    serialized_users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_approved': user.is_approved,
        'chats_count': len(user.chats)
    } for user in users]
    
    pending_users = User.query.filter_by(is_approved=False, is_admin=False).all()
    serialized_pending_users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in pending_users]
    
    tags = Tag.query.all()
    return render_template('admin.html', 
                         users=users,
                         tags=tags, 
                         pending_users=pending_users,
                         serialized_users=serialized_users,
                         serialized_pending_users=serialized_pending_users)

@app.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    
    email_sent = send_approval_email(user.email, user.username, approved=True)
    if not email_sent:
        return jsonify({'warning': 'User approved but email notification failed'}), 200
    
    return jsonify({'success': True})

@app.route('/admin/user/<int:user_id>/reject', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get_or_404(user_id)
    email_sent = send_approval_email(user.email, user.username, approved=False)
    
    db.session.delete(user)
    db.session.commit()

    if not email_sent:
        return jsonify({'warning': 'User rejected but email notification failed'}), 200
    
    return jsonify({'success': True})

@app.route('/chat')
@login_required
def chat():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    tags = Tag.query.all()
    return render_template('chat.html', chats=chats, tags=tags)

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
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/chat/<int:chat_id>/message/stream')
@login_required
def stream_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    def generate():
        try:
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
            
            all_messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp).all()
            chat.title = generate_chat_summary(all_messages)
            
            suggested_tags = suggest_tags(all_messages)
            existing_tags = Tag.query.filter(Tag.name.in_(suggested_tags)).all()
            chat.tags = list(set(chat.tags + existing_tags))
            
            db.session.commit()
            
            yield 'data: [DONE]\n\n'
        except Exception as e:
            db.session.rollback()
            yield f'data: error: {str(e)}\n\n'
            yield 'data: [DONE]\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

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
    return jsonify({
        'title': chat.title,
        'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in chat.tags]
    })

@app.route('/chat/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    Message.query.filter_by(chat_id=chat_id).delete()
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/chat/<int:chat_id>/tags', methods=['POST'])
@login_required
def update_chat_tags(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    tag_ids = request.json.get('tag_ids', [])
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()
    chat.tags = tags
    db.session.commit()
    
    return jsonify({'success': True})
