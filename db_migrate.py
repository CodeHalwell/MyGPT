from app import app, db
from sqlalchemy import text

with app.app_context():
    # Add model column to Message table if it doesn't exist
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE message ADD COLUMN IF NOT EXISTS model VARCHAR(50)'))
        conn.commit()
    print("Database migration completed successfully!")
