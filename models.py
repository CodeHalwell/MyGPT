from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import re

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    last_password_change = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Set password with additional security checks."""
        if not self._validate_password(password):
            raise ValueError("Password does not meet security requirements")
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()

    def check_password(self, password):
        """Check password with brute force protection."""
        is_valid = check_password_hash(self.password_hash, password)
        if not is_valid:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()
            db.session.commit()
        else:
            self.failed_login_attempts = 0
            self.last_failed_login = None
            db.session.commit()
        return is_valid

    def is_account_locked(self):
        """Check if account is locked due to too many failed attempts."""
        if self.failed_login_attempts >= 5 and self.last_failed_login:
            lockout_duration = datetime.utcnow() - self.last_failed_login
            if lockout_duration.total_seconds() < 300:  # 5 minutes lockout
                return True
        return False

    @staticmethod
    def _validate_password(password):
        """Validate password meets security requirements."""
        if not password or len(password) < 8:
            return False
        # Require at least one letter and one number
        return bool(re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', password))

# Keep other model classes unchanged
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default="#6c757d")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='chat_tags', backref=db.backref('chats', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    model = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for many-to-many relationship between Chat and Tag
chat_tags = db.Table('chat_tags',
    db.Column('chat_id', db.Integer, db.ForeignKey('chat.id', ondelete='CASCADE'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True)
)

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))
