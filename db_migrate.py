from app import app, db
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_schema_migrations():
    """Run schema migrations (adding columns)"""
    logger.info("Running schema migrations...")
    with db.engine.connect() as conn:
        # Detect database type
        db_type = db.engine.dialect.name
        
        try:
            if db_type == 'postgresql':
                # PostgreSQL supports IF NOT EXISTS
                conn.execute(text('ALTER TABLE message ADD COLUMN IF NOT EXISTS model VARCHAR(50)'))
                conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_token VARCHAR(100) UNIQUE'))
                conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP'))
            else:
                # SQLite - check if columns exist first
                
                # Check if model column exists in message table
                result = conn.execute(text("PRAGMA table_info(message)"))
                columns = [row[1] for row in result]
                if 'model' not in columns:
                    conn.execute(text('ALTER TABLE message ADD COLUMN model VARCHAR(50)'))
                
                # Check if reset_token column exists in user table
                result = conn.execute(text('PRAGMA table_info("user")'))
                columns = [row[1] for row in result]
                if 'reset_token' not in columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN reset_token VARCHAR(100)'))
                if 'reset_token_expiry' not in columns:
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN reset_token_expiry TIMESTAMP'))
                    
            conn.commit()
            
        except Exception as e:
            # If columns already exist, that's fine
            logger.info(f"Schema migration note: {str(e)}")
            
    logger.info("Schema migrations completed successfully!")

def run_index_migrations():
    """Run index migrations for performance optimization"""
    logger.info("Running index migrations...")
    
    with db.engine.connect() as conn:
        trans = conn.begin()
        
        try:
            # Detect database type
            db_type = db.engine.dialect.name
            logger.info(f"Database type detected: {db_type}")
            
            # User table indexes
            logger.info("Adding indexes for User table...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_user_reset_token ON "user" (reset_token)'))
            
            # Chat table indexes
            logger.info("Adding indexes for Chat table...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat (user_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat (created_at)'))
            
            # Composite index - adjust for database type
            if db_type == 'postgresql':
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat (user_id, created_at DESC)'))
            else:
                conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat (user_id, created_at)'))
            
            # Message table indexes
            logger.info("Adding indexes for Message table...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_message_chat_id ON message (chat_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_message_timestamp ON message (timestamp)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_message_chat_timestamp ON message (chat_id, timestamp)'))
            
            # Tag table indexes
            logger.info("Adding indexes for Tag table...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_tag_name ON tag (name)'))
            
            # Association table indexes
            logger.info("Adding indexes for chat_tags association table...")
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_tags_chat_id ON chat_tags (chat_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_chat_tags_tag_id ON chat_tags (tag_id)'))
            
            trans.commit()
            logger.info("Index migrations completed successfully!")
            
        except Exception as e:
            trans.rollback()
            logger.error(f"Error during index migration: {str(e)}")
            raise

with app.app_context():
    # Run schema migrations first
    run_schema_migrations()
    
    # Run index migrations
    run_index_migrations()
    
    print("Database migration completed successfully!")
