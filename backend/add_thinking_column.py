import os
from sqlalchemy import create_engine, text

def get_db_url():
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'github_daily_report')
    port = os.getenv('MYSQL_PORT', '3306')
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

def add_thinking_content_column():
    url = get_db_url()
    engine = create_engine(url)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE make_task ADD COLUMN thinking_content TEXT"))
            print("Added thinking_content column to make_task table.")
        except Exception as e:
            print(f"Error adding column (might already exist): {e}")

if __name__ == "__main__":
    add_thinking_content_column()
