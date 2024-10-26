from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        # Add new security columns to User table
        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP'))
        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0'))
        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP'))
        
        # Set NOT NULL constraints for important fields
        conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash SET NOT NULL'))
        conn.execute(text('ALTER TABLE "user" ALTER COLUMN is_admin SET NOT NULL'))
        conn.execute(text('ALTER TABLE "user" ALTER COLUMN is_approved SET NOT NULL'))
        
        # Add cascade delete to foreign keys
        conn.execute(text('ALTER TABLE chat DROP CONSTRAINT IF EXISTS chat_user_id_fkey'))
        conn.execute(text('ALTER TABLE chat ADD CONSTRAINT chat_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE'))
        
        conn.execute(text('ALTER TABLE message DROP CONSTRAINT IF EXISTS message_chat_id_fkey'))
        conn.execute(text('ALTER TABLE message ADD CONSTRAINT message_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE'))
        
        conn.execute(text('ALTER TABLE chat_tags DROP CONSTRAINT IF EXISTS chat_tags_chat_id_fkey'))
        conn.execute(text('ALTER TABLE chat_tags DROP CONSTRAINT IF EXISTS chat_tags_tag_id_fkey'))
        conn.execute(text('ALTER TABLE chat_tags ADD CONSTRAINT chat_tags_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES chat(id) ON DELETE CASCADE'))
        conn.execute(text('ALTER TABLE chat_tags ADD CONSTRAINT chat_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE'))
        
        conn.commit()
    print("Security migration completed successfully!")
