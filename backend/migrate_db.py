import os
import sys
from sqlalchemy import text

# Add current dir to path
sys.path.append(os.getcwd())

try:
    from backend.utils.db import init_engine
except ImportError:
    from utils.db import init_engine

def migrate():
    engine = init_engine()
    if not engine:
        print("No DB engine")
        return

    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE pull_record ADD COLUMN token_count INT DEFAULT 0;"))
            print("Migration successful")
        except Exception as e:
            print(f"Migration failed (maybe column exists): {e}")

if __name__ == "__main__":
    migrate()
