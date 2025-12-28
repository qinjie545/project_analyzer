import os
from sqlalchemy import create_engine, text

def drop_index():
    host = os.getenv('MYSQL_HOST', 'mysql')
    user = os.getenv('MYSQL_USER', 'appuser')
    password = os.getenv('MYSQL_PASSWORD', 'apppassword')
    database = os.getenv('MYSQL_DATABASE', 'github_daily_report')
    port = os.getenv('MYSQL_PORT', '3306')
    
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    engine = create_engine(url)
    
    with engine.connect() as conn:
        try:
            print("Attempting to drop index 'scene'...")
            conn.execute(text("DROP INDEX scene ON prompt_config"))
            print("Dropped index 'scene'")
        except Exception as e:
            print(f"Failed to drop 'scene': {e}")
            
        try:
            print("Attempting to drop index 'scene_UNIQUE'...")
            conn.execute(text("DROP INDEX scene_UNIQUE ON prompt_config"))
            print("Dropped index 'scene_UNIQUE'")
        except Exception as e:
            print(f"Failed to drop 'scene_UNIQUE': {e}")
            
        conn.commit()

if __name__ == "__main__":
    drop_index()
