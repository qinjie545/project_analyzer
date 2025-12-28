import os
from sqlalchemy import create_engine, text

def check_schema():
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', 'github_daily_report')
    port = os.getenv('MYSQL_PORT', '3306')
    
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    engine = create_engine(url)
    
    with engine.connect() as conn:
        result = conn.execute(text("DESCRIBE make_task"))
        columns = [row[0] for row in result]
        print(f"Columns in make_task: {columns}")
        
        for row in result:
            if row[0] == 'thinking_content':
                print(f"thinking_content type: {row[1]}")

if __name__ == "__main__":
    check_schema()
