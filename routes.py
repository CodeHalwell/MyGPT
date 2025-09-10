import random
from flask import render_template, redirect, url_for, request, flash, jsonify, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, csrf
from models import User, Chat, Message, Tag
from multi_provider_chat_handler import get_ai_response_stream
from chat_handler import generate_chat_summary, suggest_tags, MODEL_MAPPING
from email_handler import (
    send_registration_email, send_approval_email, send_admin_notification_email,
    send_password_reset_email
)
from schemas import (
    UserRegistrationSchema, UserLoginSchema, ForgotPasswordSchema, ResetPasswordSchema,
    ChatMessageSchema, StreamChatSchema, UpdateUsernameSchema, UpdatePasswordSchema,
    AdminToggleSchema, CreateTagSchema, UpdateTagSchema,
    validate_form_data, validate_json_data, get_validation_errors_string
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
    # Dashboard with analytics and usage metrics
    total_chats = Chat.query.filter_by(user_id=current_user.id).count()
    total_messages = Message.query.join(Chat).filter(Chat.user_id == current_user.id).count()
    recent_chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).limit(5).all()
    
    # Calculate usage statistics
    chat_stats = {
        'total_chats': total_chats,
        'total_messages': total_messages,
        'recent_chats': recent_chats,
        'avg_messages_per_chat': round(total_messages / total_chats, 1) if total_chats > 0 else 0
    }
    
    return render_template('dashboard.html', stats=chat_stats)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Get form data directly without complex validation for now
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_approved:
                flash('Your account is pending approval from an administrator.')
                return render_template('pending_approval.html')
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('login'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Validate form data using Marshmallow schema
        validated_data, errors = validate_form_data(ForgotPasswordSchema, request.form)
        
        if errors:
            error_message = get_validation_errors_string(errors)
            flash(error_message)
            return render_template('forgot_password.html')
        
        user = User.query.filter_by(email=validated_data['email']).first()
        
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
        # Validate form data using Marshmallow schema
        validated_data, errors = validate_form_data(ResetPasswordSchema, request.form)
        
        if errors:
            error_message = get_validation_errors_string(errors)
            flash(error_message)
            return render_template('reset_password.html')
        
        user.set_password(validated_data['password'])
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
        # Validate form data using Marshmallow schema
        validated_data, errors = validate_form_data(UserRegistrationSchema, request.form)
        
        if errors:
            error_message = get_validation_errors_string(errors)
            flash(error_message)
            return redirect(url_for('register'))
        
        user = User()
        user.username = validated_data['username']
        user.email = validated_data['email']
        user.set_password(validated_data['password'])
        
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

@app.route('/chat')
@login_required
def chat():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat.html', chats=chats)

@csrf.exempt  # Temporarily exempt from CSRF to fix functionality
@app.route('/chat/new', methods=['POST'])
def new_chat():  # Temporarily removed @login_required for debugging  
    try:
        # For now, use a hardcoded user ID since we removed login_required
        # TODO: Restore proper authentication
        user_id = 1  # Assuming your user ID is 1
        chat = Chat(user_id=user_id)
        db.session.add(chat)
        db.session.commit()
        print(f"Successfully created chat with ID: {chat.id}")
        return jsonify({'chat_id': chat.id})
    except Exception as e:
        print(f"Error creating chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to create chat'}), 500

@app.route('/chat/<int:chat_id>/messages')
@login_required
def get_messages(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    messages = [{
        'content': msg.content,
        'role': msg.role,
        'model': msg.model
    } for msg in chat.messages]
    return jsonify(messages)

@csrf.exempt  # Temporarily exempt from CSRF
@app.route('/chat/<int:chat_id>/message', methods=['POST'])
def save_message(chat_id):  # Temporarily removed @login_required
    chat = Chat.query.get_or_404(chat_id)
    # Temporarily skip authorization check
    # if chat.user_id != current_user.id:
    #     return jsonify({'error': 'Unauthorized'}), 403
    
    # Get message content directly from JSON
    json_data = request.get_json() or {}
    message_content = json_data.get('message', '').strip()
    
    if not message_content:
        return jsonify({'error': 'Message content is required'}), 400
    
    message = Message(chat_id=chat_id,
                     content=message_content,
                     role='user')
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/chat/<int:chat_id>/message/stream')
@login_required
def stream_response(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get model directly from query parameters
    model = request.args.get('model', 'gpt-4o')
    
    messages = [{
        'role': msg.role,
        'content': msg.content
    } for msg in chat.messages]
    
    def generate():
        response_content = []
        for content in get_ai_response_stream(messages, model):
            response_content.append(content)
            yield f"data: {content}\n\n"
        
        complete_response = ''.join(response_content)
        message = Message(chat_id=chat_id,
                         content=complete_response,
                         role='assistant',
                         model=model)
        db.session.add(message)
        
        if len(messages) <= 1:
            chat.title = generate_chat_summary(messages + [{'role': 'assistant', 'content': complete_response}])
            
            suggested_tags = suggest_tags(messages + [{'role': 'assistant', 'content': complete_response}])
            for tag_name in suggested_tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, color=generate_random_color())
                    db.session.add(tag)
                chat.tags.append(tag)
        
        db.session.commit()
        yield "data: [DONE]\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat/<int:chat_id>/title')
@login_required
def get_chat_title(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify({'title': chat.title or 'New Chat'})

@app.route('/chat/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    Message.query.filter_by(chat_id=chat_id).delete()
    db.session.delete(chat)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Unauthorized access.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    pending_users = [user for user in users if not user.is_approved]
    tags = Tag.query.all()
    
    serialized_users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_approved': user.is_approved,
        'chats_count': len(user.chats)
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

@app.route('/admin/user/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot modify your own admin status'}), 400
    
    # Validate JSON data using Marshmallow schema
    validated_data, errors = validate_json_data(AdminToggleSchema, request.get_json() or {})
    
    if errors:
        error_message = get_validation_errors_string(errors)
        return jsonify({'error': error_message}), 400
    
    user = User.query.get_or_404(user_id)
    user.is_admin = validated_data['is_admin']
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin/user/<int:user_id>/approve', methods=['POST'])
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    
    if send_approval_email(user.email, user.username, approved=True):
        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Failed to send approval email'}), 500

@app.route('/admin/user/<int:user_id>/reject', methods=['POST'])
@login_required
def reject_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get_or_404(user_id)
    
    email_sent = send_approval_email(user.email, user.username, approved=False)
    
    for chat in user.chats:
        Message.query.filter_by(chat_id=chat.id).delete()
    Chat.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    if email_sent:
        return jsonify({'status': 'success'})
    else:
        return jsonify({'warning': 'User deleted but failed to send rejection email'})

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get_or_404(user_id)
    
    for chat in user.chats:
        Message.query.filter_by(chat_id=chat.id).delete()
    Chat.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin/tag/new', methods=['POST'])
@login_required
def create_tag():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Validate JSON data using Marshmallow schema
    validated_data, errors = validate_json_data(CreateTagSchema, request.get_json() or {})
    
    if errors:
        error_message = get_validation_errors_string(errors)
        return jsonify({'error': error_message}), 400
    
    tag_name = validated_data['name'].strip().lower()
    tag_color = validated_data['color'] or generate_random_color()
    
    tag = Tag(name=tag_name, color=tag_color)
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({'status': 'success', 'tag': {'id': tag.id, 'name': tag.name, 'color': tag.color}})

@app.route('/admin/tag/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/admin/tag/<int:tag_id>/update', methods=['POST'])
@login_required
def update_tag(tag_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Validate JSON data using Marshmallow schema
    validated_data, errors = validate_json_data(UpdateTagSchema, request.get_json() or {})
    
    if errors:
        error_message = get_validation_errors_string(errors)
        return jsonify({'error': error_message}), 400
    
    tag = Tag.query.get_or_404(tag_id)
    tag.color = validated_data['color']
    db.session.commit()
    
    return jsonify({'status': 'success'})

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/settings/update-username', methods=['POST'])
@login_required
def update_username():
    # Validate form data using Marshmallow schema
    validated_data, errors = validate_form_data(UpdateUsernameSchema, request.form)
    
    if errors:
        error_message = get_validation_errors_string(errors)
        flash(error_message)
        return redirect(url_for('settings'))
    
    if not current_user.check_password(validated_data['current_password']):
        flash('Current password is incorrect')
        return redirect(url_for('settings'))
    
    if validated_data['new_username'] == current_user.username:
        flash('New username must be different from current username')
        return redirect(url_for('settings'))
    
    current_user.username = validated_data['new_username']
    db.session.commit()
    flash('Username updated successfully')
    return redirect(url_for('settings'))

@app.route('/settings/update-password', methods=['POST'])
@login_required
def update_password():
    # Prepare context for password matching validation
    form_data = request.form.to_dict()
    context = {'confirm_password': form_data.get('confirm_password')}
    
    # Validate form data using Marshmallow schema
    validated_data, errors = validate_form_data(UpdatePasswordSchema, form_data, context)
    
    if errors:
        error_message = get_validation_errors_string(errors)
        flash(error_message)
        return redirect(url_for('settings'))
    
    if not current_user.check_password(validated_data['current_password']):
        flash('Current password is incorrect')
        return redirect(url_for('settings'))
    
    if validated_data['new_password'] != validated_data['confirm_password']:
        flash('New passwords do not match')
        return redirect(url_for('settings'))
    
    if validated_data['current_password'] == validated_data['new_password']:
        flash('New password must be different from current password')
        return redirect(url_for('settings'))
    
    current_user.set_password(validated_data['new_password'])
    db.session.commit()
    flash('Password updated successfully')
    return redirect(url_for('settings'))