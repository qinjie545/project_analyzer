import os
from sqlalchemy import create_engine, text

# Get env vars
user = os.getenv('MYSQL_USER', 'appuser')
password = os.getenv('MYSQL_PASSWORD', 'apppassword')
host = os.getenv('MYSQL_HOST', 'mysql')
port = os.getenv('MYSQL_PORT', '3306')
dbname = os.getenv('MYSQL_DATABASE', 'github_daily_report')

# Connect
db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}"
engine = create_engine(db_url)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM llm_config WHERE is_active=1"))
        rows = result.fetchall()
        print(f"Active configs: {len(rows)}")
        for row in rows:
            print(f"Provider: {row.provider}, Model: {row.model_name}, BaseURL: {row.base_url}")
            # Don't print full key for security, just length
            print(f"API Key length: {len(row.api_key) if row.api_key else 0}")
except Exception as e:
    print(f"Error: {e}")
