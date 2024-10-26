from app import app, db
from sqlalchemy import text

with app.app_context():
    # Add model column to Message table if it doesn't exist
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE message ADD COLUMN IF NOT EXISTS model VARCHAR(50)'))
        # Add reset token columns to User table
        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_token VARCHAR(100) UNIQUE'))
        conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP'))
        conn.commit()
    print("Database migration completed successfully!")
