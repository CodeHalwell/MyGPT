"""
Test configuration for MyGPT application.
Provides shared fixtures for all tests.
"""
import pytest
import tempfile
import os

# Set testing environment variables before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'

from app import create_app, db
from models import User, Chat, Message, Tag


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to serve as the database
    db_fd, db_path = tempfile.mkstemp()
    
    # Override configuration for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'LOGIN_DISABLED': True,
        'SESSION_COOKIE_SECURE': False,
        'REMEMBER_COOKIE_SECURE': False,
    }
    
    # Create app with test config
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up the temporary database file
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    user = User(
        username='testuser',
        email='test@example.com',
        is_admin=False,
        is_approved=True
    )
    user.set_password('testpassword')
    return user


@pytest.fixture
def admin_user():
    """Create an admin user for testing."""
    user = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        is_approved=True
    )
    user.set_password('adminpassword')
    return user


@pytest.fixture
def sample_tag():
    """Create a sample tag for testing."""
    return Tag(name='test-tag', color='#ff0000')


@pytest.fixture
def sample_chat(sample_user):
    """Create a sample chat for testing."""
    return Chat(
        user_id=sample_user.id,
        title='Test Chat'
    )


@pytest.fixture
def sample_message(sample_chat):
    """Create a sample message for testing."""
    return Message(
        chat_id=sample_chat.id,
        content='Hello, this is a test message',
        role='user'
    )