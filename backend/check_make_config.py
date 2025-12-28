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
        result = conn.execute(text("SELECT * FROM make_config ORDER BY updated_at DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"Provider: {row.provider}")
            print(f"Model: {row.model}")
            print(f"BaseURL: {row.base_url}")
            print(f"API Key length: {len(row.external_api_key) if row.external_api_key else 0}")
        else:
            print("No config found in make_config")
except Exception as e:
    print(f"Error: {e}")
