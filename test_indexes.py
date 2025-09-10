"""
Test script to verify database indexes are working correctly
"""

import time
import logging
from app import app, db
from models import User, Chat, Message, Tag
from sqlalchemy import text
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_index_performance():
    """Test that indexes improve query performance"""
    
    with app.app_context():
        try:
            # Test User table queries
            logger.info("Testing User table query performance...")
            
            # Test username lookup (login)
            start_time = time.time()
            user = User.query.filter_by(username='testuser').first()
            username_time = time.time() - start_time
            logger.info(f"Username lookup time: {username_time:.4f} seconds")
            
            # Test email lookup (registration/password reset)
            start_time = time.time()
            user = User.query.filter_by(email='test@example.com').first()
            email_time = time.time() - start_time
            logger.info(f"Email lookup time: {email_time:.4f} seconds")
            
            # Test Chat table queries
            logger.info("Testing Chat table query performance...")
            
            # Test user's chats query (most common)
            start_time = time.time()
            chats = Chat.query.filter_by(user_id=1).order_by(Chat.created_at.desc()).limit(10).all()
            user_chats_time = time.time() - start_time
            logger.info(f"User chats lookup time: {user_chats_time:.4f} seconds")
            
            # Test Message table queries
            logger.info("Testing Message table query performance...")
            
            # Test chat messages query (very common)
            start_time = time.time()
            messages = Message.query.filter_by(chat_id=1).order_by(Message.timestamp).all()
            chat_messages_time = time.time() - start_time
            logger.info(f"Chat messages lookup time: {chat_messages_time:.4f} seconds")
            
            # Test Tag table queries
            logger.info("Testing Tag table query performance...")
            
            # Test tag name lookup
            start_time = time.time()
            tag = Tag.query.filter_by(name='testtag').first()
            tag_lookup_time = time.time() - start_time
            logger.info(f"Tag name lookup time: {tag_lookup_time:.4f} seconds")
            
            logger.info("Index performance test completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during performance test: {str(e)}")

def test_query_plans():
    """Test query execution plans to verify indexes are being used"""
    
    with app.app_context():
        try:
            logger.info("Testing query execution plans...")
            
            with db.engine.connect() as conn:
                # Detect database type
                db_type = db.engine.dialect.name
                
                if db_type == 'postgresql':
                    # Test username lookup plan
                    result = conn.execute(text("""
                        EXPLAIN (ANALYZE, BUFFERS) 
                        SELECT * FROM "user" WHERE username = 'testuser'
                    """))
                    
                    logger.info("Username lookup query plan:")
                    for row in result:
                        logger.info(f"  {row[0]}")
                    
                    # Test user's chats query plan
                    result = conn.execute(text("""
                        EXPLAIN (ANALYZE, BUFFERS)
                        SELECT * FROM chat WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10
                    """))
                    
                    logger.info("User chats query plan:")
                    for row in result:
                        logger.info(f"  {row[0]}")
                    
                    # Test chat messages query plan
                    result = conn.execute(text("""
                        EXPLAIN (ANALYZE, BUFFERS)
                        SELECT * FROM message WHERE chat_id = 1 ORDER BY timestamp
                    """))
                    
                    logger.info("Chat messages query plan:")
                    for row in result:
                        logger.info(f"  {row[0]}")
                        
                elif db_type == 'sqlite':
                    # Test username lookup plan
                    result = conn.execute(text("""
                        EXPLAIN QUERY PLAN
                        SELECT * FROM "user" WHERE username = 'testuser'
                    """))
                    
                    logger.info("Username lookup query plan:")
                    for row in result:
                        logger.info(f"  {row[3]}")
                    
                    # Test user's chats query plan
                    result = conn.execute(text("""
                        EXPLAIN QUERY PLAN
                        SELECT * FROM chat WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10
                    """))
                    
                    logger.info("User chats query plan:")
                    for row in result:
                        logger.info(f"  {row[3]}")
                    
                    # Test chat messages query plan
                    result = conn.execute(text("""
                        EXPLAIN QUERY PLAN
                        SELECT * FROM message WHERE chat_id = 1 ORDER BY timestamp
                    """))
                    
                    logger.info("Chat messages query plan:")
                    for row in result:
                        logger.info(f"  {row[3]}")
                else:
                    logger.warning(f"Query plan analysis not supported for database type: {db_type}")
            
            logger.info("Query plan analysis completed!")
            
        except Exception as e:
            logger.error(f"Error during query plan test: {str(e)}")

def verify_indexes_exist():
    """Verify that all expected indexes exist"""
    
    expected_indexes = [
        'idx_user_username',
        'idx_user_email', 
        'idx_user_reset_token',
        'idx_chat_user_id',
        'idx_chat_created_at',
        'idx_chat_user_created',
        'idx_message_chat_id',
        'idx_message_timestamp',
        'idx_message_chat_timestamp',
        'idx_tag_name',
        'idx_chat_tags_chat_id',
        'idx_chat_tags_tag_id'
    ]
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Detect database type
                db_type = db.engine.dialect.name
                
                if db_type == 'postgresql':
                    result = conn.execute(text("""
                        SELECT indexname FROM pg_indexes 
                        WHERE schemaname = 'public' 
                        AND indexname LIKE 'idx_%'
                    """))
                    existing_indexes = [row[0] for row in result]
                    
                elif db_type == 'sqlite':
                    result = conn.execute(text("""
                        SELECT name FROM sqlite_master 
                        WHERE type='index' 
                        AND name LIKE 'idx_%'
                    """))
                    existing_indexes = [row[0] for row in result]
                else:
                    logger.error(f"Unsupported database type: {db_type}")
                    return False
                
                logger.info("Verifying indexes exist...")
                all_exist = True
                
                for index_name in expected_indexes:
                    if index_name in existing_indexes:
                        logger.info(f"✓ {index_name} exists")
                    else:
                        logger.error(f"✗ {index_name} missing")
                        all_exist = False
                
                if all_exist:
                    logger.info("All expected indexes exist!")
                else:
                    logger.error("Some indexes are missing!")
                
                return all_exist
                
        except Exception as e:
            logger.error(f"Error verifying indexes: {str(e)}")
            return False

def create_test_data():
    """Create minimal test data to verify indexes work"""
    
    with app.app_context():
        try:
            # Check if test user already exists
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                logger.info("Creating test data...")
                
                # Create test user
                test_user = User(
                    username='testuser',
                    email='test@example.com',
                    is_approved=True
                )
                test_user.set_password('testpass')
                db.session.add(test_user)
                
                # Create test tag
                test_tag = Tag(name='testtag', color='#ff0000')
                db.session.add(test_tag)
                
                db.session.commit()
                
                # Create test chat
                test_chat = Chat(
                    user_id=test_user.id,
                    title='Test Chat',
                    created_at=datetime.utcnow()
                )
                db.session.add(test_chat)
                db.session.commit()
                
                # Create test message
                test_message = Message(
                    chat_id=test_chat.id,
                    content='Test message',
                    role='user',
                    timestamp=datetime.utcnow()
                )
                db.session.add(test_message)
                db.session.commit()
                
                logger.info("Test data created successfully!")
            else:
                logger.info("Test data already exists, skipping creation.")
                
        except Exception as e:
            logger.error(f"Error creating test data: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting database index tests...")
    
    # Create test data
    create_test_data()
    
    # Verify indexes exist
    if verify_indexes_exist():
        # Test performance
        test_index_performance()
        
        # Test query plans
        test_query_plans()
    else:
        logger.error("Cannot run performance tests - indexes missing!")
    
    logger.info("Index testing completed!")