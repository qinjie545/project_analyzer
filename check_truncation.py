import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get DB connection string from env or use default
# Assuming running inside the container or with port mapping
# The user said "docker 启动下", so I should probably use the docker container to run this or connect to localhost:3306 if mapped.
# The docker-compose.yml usually maps 3306:3306.
# Let's try connecting to localhost first.

DATABASE_URL = "mysql+pymysql://appuser:appuser-pass@mysql:3306/github_daily_report"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Check column type
        result = connection.execute(text("DESCRIBE make_task"))
        for row in result:
            print(f"Column: {row[0]}, Type: {row[1]}")
            
        # Get the latest task
        result = connection.execute(text("SELECT id, repo_name, LENGTH(detailed_content) as content_len, detailed_content FROM make_task ORDER BY created_at DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            print(f"ID: {row[0]}")
            print(f"Repo: {row[1]}")
            print(f"Content Length (bytes): {row[2]}")
            content = row[3]
            if content:
                print(f"Last 100 chars: {content[-100:]}")
            else:
                print("Content is None")
        else:
            print("No tasks found.")

except Exception as e:
    print(f"Error: {e}")
