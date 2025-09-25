"""
Test configuration for MyGPT application.
Provides shared fixtures for all tests.
"""
import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# Set testing environment variables before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
os.environ['FLASK_ENV'] = 'testing'

from mygpt.app import create_app, db
from mygpt.models import User, Chat, Message, Tag


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to serve as the database
    db_fd, db_path = tempfile.mkstemp()
    
    # Create app with test config
    app = create_app('testing')
    
    # Override any additional test settings
    app.config.update({
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
    })
    
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