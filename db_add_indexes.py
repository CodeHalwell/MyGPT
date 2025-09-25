"""
Database migration to add performance indexes
This script adds critical indexes to improve query performance for frequently accessed columns.
"""

import logging

from sqlalchemy import text

from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_database_indexes():
    """Add critical database indexes for performance optimization"""

    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Start transaction
                trans = conn.begin()

                try:
                    logger.info(
                        "Adding database indexes for performance optimization..."
                    )

                    # Detect database type
                    db_type = db.engine.dialect.name
                    logger.info(f"Database type detected: {db_type}")

                    # User table indexes
                    logger.info("Adding indexes for User table...")

                    # Index on username for login lookups (if not already exists)
                    if db_type == "postgresql":
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username)'
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_username ON "user" (username)'
                            )
                        )

                    # Index on email for registration/password reset lookups
                    if db_type == "postgresql":
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email)'
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_email ON "user" (email)'
                            )
                        )

                    # Index on reset_token for password reset lookups
                    if db_type == "postgresql":
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_reset_token ON "user" (reset_token)'
                            )
                        )
                    else:
                        conn.execute(
                            text(
                                'CREATE INDEX IF NOT EXISTS idx_user_reset_token ON "user" (reset_token)'
                            )
                        )

                    # Chat table indexes
                    logger.info("Adding indexes for Chat table...")

                    # Index on user_id for user's chat listings (high priority)
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_chat_user_id ON chat (user_id)"
                        )
                    )

                    # Index on created_at for ordering chats
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_chat_created_at ON chat (created_at)"
                        )
                    )

                    # Composite index on user_id and created_at for user's recent chats
                    if db_type == "postgresql":
                        conn.execute(
                            text(
                                "CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat (user_id, created_at DESC)"
                            )
                        )
                    else:
                        # SQLite doesn't support DESC in index definition the same way
                        conn.execute(
                            text(
                                "CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat (user_id, created_at)"
                            )
                        )

                    # Message table indexes
                    logger.info("Adding indexes for Message table...")

                    # Index on chat_id for message retrieval (high priority)
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_message_chat_id ON message (chat_id)"
                        )
                    )

                    # Index on timestamp for message ordering
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_message_timestamp ON message (timestamp)"
                        )
                    )

                    # Composite index on chat_id and timestamp for chat message ordering
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_message_chat_timestamp ON message (chat_id, timestamp)"
                        )
                    )

                    # Tag table indexes
                    logger.info("Adding indexes for Tag table...")

                    # Index on name for tag lookups
                    conn.execute(
                        text("CREATE INDEX IF NOT EXISTS idx_tag_name ON tag (name)")
                    )

                    # Association table indexes
                    logger.info("Adding indexes for chat_tags association table...")

                    # Index on chat_id for tag lookups by chat
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_chat_tags_chat_id ON chat_tags (chat_id)"
                        )
                    )

                    # Index on tag_id for chat lookups by tag
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_chat_tags_tag_id ON chat_tags (tag_id)"
                        )
                    )

                    # Commit transaction
                    trans.commit()
                    logger.info("Successfully added all database indexes!")

                except Exception as e:
                    # Rollback on error
                    trans.rollback()
                    logger.error(f"Error adding indexes: {str(e)}")
                    raise

        except Exception as e:
            logger.error(f"Failed to add database indexes: {str(e)}")
            raise


def list_existing_indexes():
    """List existing indexes for verification"""

    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Detect database type and query for existing indexes
                db_type = db.engine.dialect.name

                if db_type == "postgresql":
                    result = conn.execute(
                        text(
                            """
                        SELECT 
                            schemaname,
                            tablename,
                            indexname,
                            indexdef
                        FROM pg_indexes 
                        WHERE schemaname = 'public'
                        ORDER BY tablename, indexname
                    """
                        )
                    )

                    logger.info("Existing database indexes:")
                    for row in result:
                        logger.info(
                            f"  {row.tablename}.{row.indexname}: {row.indexdef}"
                        )

                elif db_type == "sqlite":
                    # Get list of tables first
                    tables_result = conn.execute(
                        text(
                            """
                        SELECT name FROM sqlite_master WHERE type='table'
                    """
                        )
                    )

                    logger.info("Existing database indexes:")
                    for table_row in tables_result:
                        table_name = table_row[0]

                        # Get indexes for this table
                        indexes_result = conn.execute(
                            text(
                                f"""
                            SELECT name, sql FROM sqlite_master 
                            WHERE type='index' AND tbl_name='{table_name}'
                            AND name NOT LIKE 'sqlite_%'
                        """
                            )
                        )

                        for index_row in indexes_result:
                            index_name = index_row[0]
                            index_sql = index_row[1] or "Auto-generated"
                            logger.info(f"  {table_name}.{index_name}: {index_sql}")
                else:
                    logger.warning(
                        f"Unsupported database type for index listing: {db_type}"
                    )

        except Exception as e:
            logger.error(f"Error listing indexes: {str(e)}")


if __name__ == "__main__":
    logger.info("Starting database index migration...")

    # List existing indexes first
    logger.info("Listing existing indexes before migration:")
    try:
        list_existing_indexes()
    except Exception as e:
        logger.warning(f"Could not list existing indexes: {str(e)}")

    # Add new indexes
    add_database_indexes()

    # List indexes after migration
    logger.info("Listing indexes after migration:")
    try:
        list_existing_indexes()
    except Exception as e:
        logger.warning(f"Could not list indexes after migration: {str(e)}")

    logger.info("Database index migration completed!")
