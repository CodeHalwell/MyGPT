"""
Tests for database models.
"""

from datetime import datetime, timedelta

import pytest

from app import db
from models import Chat, Message, Tag, User, chat_tags


class TestUser:
    """Test cases for the User model."""

    def test_user_creation(self, app, sample_user):
        """Test basic user creation."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            user = db.session.get(User, sample_user.id)
            assert user is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.is_admin is False
            assert user.is_approved is True

    def test_password_hashing(self, app, sample_user):
        """Test password hashing and verification."""
        with app.app_context():
            # Password should be hashed, not stored in plain text
            assert sample_user.password_hash is not None
            assert sample_user.password_hash != "testpassword"

            # Should be able to verify correct password
            assert sample_user.check_password("testpassword") is True
            assert sample_user.check_password("wrongpassword") is False

    def test_user_uniqueness(self, app):
        """Test that username and email are unique."""
        with app.app_context():
            user1 = User(username="unique", email="unique@test.com")
            user1.set_password("password")
            db.session.add(user1)
            db.session.commit()

            # Try to create another user with same username
            user2 = User(username="unique", email="different@test.com")
            user2.set_password("password")
            db.session.add(user2)

            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()

    def test_user_chats_relationship(self, app, sample_user):
        """Test the relationship between User and Chat."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            # Create chats for the user
            chat1 = Chat(user_id=sample_user.id, title="Chat 1")
            chat2 = Chat(user_id=sample_user.id, title="Chat 2")
            db.session.add_all([chat1, chat2])
            db.session.commit()

            # Test relationship
            user = db.session.get(User, sample_user.id)
            assert len(user.chats) == 2
            assert chat1 in user.chats
            assert chat2 in user.chats


class TestTag:
    """Test cases for the Tag model."""

    def test_tag_creation(self, app, sample_tag):
        """Test basic tag creation."""
        with app.app_context():
            db.session.add(sample_tag)
            db.session.commit()

            tag = db.session.get(Tag, sample_tag.id)
            assert tag is not None
            assert tag.name == "test-tag"
            assert tag.color == "#ff0000"
            assert tag.created_at is not None

    def test_tag_default_color(self, app):
        """Test that tag has default color."""
        with app.app_context():
            tag = Tag(name="default-color-tag")
            db.session.add(tag)
            db.session.commit()

            assert tag.color == "#6c757d"  # Default Bootstrap secondary color

    def test_tag_uniqueness(self, app):
        """Test that tag names are unique."""
        with app.app_context():
            tag1 = Tag(name="duplicate")
            db.session.add(tag1)
            db.session.commit()

            tag2 = Tag(name="duplicate")
            db.session.add(tag2)

            with pytest.raises(Exception):  # Should raise integrity error
                db.session.commit()


class TestChat:
    """Test cases for the Chat model."""

    def test_chat_creation(self, app, sample_user):
        """Test basic chat creation."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            saved_chat = db.session.get(Chat, chat.id)
            assert saved_chat is not None
            assert saved_chat.title == "Test Chat"
            assert saved_chat.user_id == sample_user.id
            assert saved_chat.created_at is not None

    def test_chat_user_relationship(self, app, sample_user):
        """Test the relationship between Chat and User."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            # Test relationship
            assert chat.user == sample_user

    def test_chat_messages_relationship(self, app, sample_user):
        """Test the relationship between Chat and Message."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            # Create messages for the chat
            msg1 = Message(chat_id=chat.id, content="Message 1", role="user")
            msg2 = Message(chat_id=chat.id, content="Message 2", role="assistant")
            db.session.add_all([msg1, msg2])
            db.session.commit()

            # Test relationship
            saved_chat = db.session.get(Chat, chat.id)
            assert len(saved_chat.messages) == 2
            assert msg1 in saved_chat.messages
            assert msg2 in saved_chat.messages

    def test_chat_tags_relationship(self, app, sample_user):
        """Test the many-to-many relationship between Chat and Tag."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            tag1 = Tag(name="tag1")
            tag2 = Tag(name="tag2")

            db.session.add_all([chat, tag1, tag2])
            db.session.commit()

            # Add tags to chat
            chat.tags.append(tag1)
            chat.tags.append(tag2)
            db.session.commit()

            # Test relationship
            saved_chat = db.session.get(Chat, chat.id)
            assert len(saved_chat.tags) == 2
            assert tag1 in saved_chat.tags
            assert tag2 in saved_chat.tags

            # Test reverse relationship
            saved_tag1 = db.session.get(Tag, tag1.id)
            assert chat in saved_tag1.chats


class TestMessage:
    """Test cases for the Message model."""

    def test_message_creation(self, app, sample_user):
        """Test basic message creation."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            message = Message(
                chat_id=chat.id, content="Hello world", role="user", model="gpt-4"
            )
            db.session.add(message)
            db.session.commit()

            saved_message = db.session.get(Message, message.id)
            assert saved_message is not None
            assert saved_message.content == "Hello world"
            assert saved_message.role == "user"
            assert saved_message.model == "gpt-4"
            assert saved_message.chat_id == chat.id
            assert saved_message.timestamp is not None

    def test_message_chat_relationship(self, app, sample_user):
        """Test the relationship between Message and Chat."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            message = Message(chat_id=chat.id, content="Test message", role="user")
            db.session.add(message)
            db.session.commit()

            # Test relationship
            assert message.chat == chat

    def test_message_role_values(self, app, sample_user):
        """Test that message role accepts expected values."""
        with app.app_context():
            db.session.add(sample_user)
            db.session.commit()

            chat = Chat(user_id=sample_user.id, title="Test Chat")
            db.session.add(chat)
            db.session.commit()

            # Test user role
            user_msg = Message(chat_id=chat.id, content="User message", role="user")
            db.session.add(user_msg)
            db.session.commit()

            # Test assistant role
            assistant_msg = Message(
                chat_id=chat.id, content="Assistant message", role="assistant"
            )
            db.session.add(assistant_msg)
            db.session.commit()

            saved_user_msg = db.session.get(Message, user_msg.id)
            saved_assistant_msg = db.session.get(Message, assistant_msg.id)

            assert saved_user_msg.role == "user"
            assert saved_assistant_msg.role == "assistant"
