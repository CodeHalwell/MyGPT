from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Chat, Message, Tag
from chat_handler import get_ai_response_stream, generate_chat_summary, suggest_tags
from email_handler import send_registration_email, send_approval_email, send_admin_notification_email

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
            # Send registration confirmation to user
            email_sent = send_registration_email(user.email, user.username)
            if not email_sent:
                flash('Registration successful but email notification could not be sent.')
            else:
                flash('Your registration is pending approval from an administrator. You will receive an email when your account is approved.')
            
            # Send notification to admin
            admin_notified = send_admin_notification_email(user.email, user.username)
            if not admin_notified:
                app.logger.error(f"Failed to send admin notification for new user registration: {user.username}")
        
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
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/chat')
@login_required
def chat():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat.html', chats=chats)

@app.route('/chat/new', methods=['POST'])
@login_required
def create_chat():
    try:
        chat = Chat(user_id=current_user.id, title="New Chat")
        db.session.add(chat)
        db.session.commit()
        
        return jsonify({
            'chat_id': chat.id,
            'title': chat.title
        })
    except Exception as e:
        app.logger.error(f"Error creating chat: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create chat'}), 500

@app.route('/chat/<int:chat_id>/message', methods=['POST'])
@login_required
def save_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        message = Message(
            chat_id=chat_id,
            content=data['message'],
            role='user'
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({'message': 'Message saved successfully'})
    except Exception as e:
        app.logger.error(f"Error saving message: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to save message'}), 500

@app.route('/chat/<int:chat_id>/message/stream')
@login_required
def stream_ai_response(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    model = request.args.get('model', 'gpt-3.5-turbo')
    messages = [{'role': m.role, 'content': m.content} for m in chat.messages]
    
    def generate():
        try:
            for token in get_ai_response_stream(messages, model=model):
                yield f"data: {token}\n\n"
                
            # Save the complete AI response
            complete_response = "".join(get_ai_response_stream(messages, model=model))
            message = Message(
                chat_id=chat_id,
                content=complete_response,
                role='assistant'
            )
            db.session.add(message)
            
            # Update chat title after first exchange if it's still default
            if chat.title == "New Chat" and len(chat.messages) <= 2:
                chat.title = generate_chat_summary(messages + [{'role': 'assistant', 'content': complete_response}])
            
            # Generate and add tags
            if len(chat.messages) <= 2:
                new_tags = suggest_tags(messages + [{'role': 'assistant', 'content': complete_response}])
                for tag_name in new_tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    if tag not in chat.tags:
                        chat.tags.append(tag)
            
            db.session.commit()
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            app.logger.error(f"Error in stream_ai_response: {str(e)}")
            db.session.rollback()
            yield f"data: Error generating response: {str(e)}\n\n"
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat/<int:chat_id>/title')
@login_required
def get_chat_title(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'title': chat.title})

@app.route('/chat/<int:chat_id>/messages')
@login_required
def get_chat_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    messages = [{'content': m.content, 'role': m.role} for m in chat.messages]
    return jsonify(messages)

@app.route('/chat/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    try:
        chat = Chat.query.get_or_404(chat_id)
        if chat.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        Message.query.filter_by(chat_id=chat.id).delete()
        chat.tags = []
        db.session.delete(chat)
        db.session.commit()
        
        return jsonify({'message': 'Chat deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting chat: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete chat'}), 500

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

@app.route('/admin/tag/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        tag = Tag.query.get_or_404(tag_id)
        
        # Remove tag from all chats
        for chat in tag.chats:
            chat.tags.remove(tag)
            
        db.session.delete(tag)
        db.session.commit()
        
        return jsonify({'message': 'Tag deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting tag: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/tag/<int:tag_id>/update', methods=['POST'])
@login_required
def update_tag(tag_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        tag = Tag.query.get_or_404(tag_id)
        data = request.get_json()
        
        if 'color' in data:
            tag.color = data['color']
            
        db.session.commit()
        return jsonify({'message': 'Tag updated successfully'})
    except Exception as e:
        app.logger.error(f"Error updating tag: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        if user.is_approved:
            return jsonify({'error': 'User is already approved'}), 400
        if user.is_admin:
            return jsonify({'error': 'Admin users are auto-approved'}), 400
        
        user.is_approved = True
        db.session.commit()
        
        # Send approval email
        email_sent = send_approval_email(user.email, user.username, approved=True)
        if not email_sent:
            app.logger.error(f"Failed to send approval email to user: {user.username}")
        
        return jsonify({'message': 'User approved successfully'})
    except Exception as e:
        app.logger.error(f"Error approving user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/user/<int:user_id>/reject', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        if user.is_admin:
            return jsonify({'error': 'Cannot reject admin users'}), 400
        
        user_email = user.email
        username = user.username
        
        for chat in user.chats:
            Message.query.filter_by(chat_id=chat.id).delete()
            db.session.delete(chat)
        
        db.session.delete(user)
        db.session.commit()
        
        send_approval_email(user_email, username, approved=False)
        
        return jsonify({'message': 'User rejected successfully'})
    except Exception as e:
        app.logger.error(f"Error rejecting user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        if user.is_admin:
            return jsonify({'error': 'Cannot delete admin users'}), 400
        
        for chat in user.chats:
            Message.query.filter_by(chat_id=chat.id).delete()
            db.session.delete(chat)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting user: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
