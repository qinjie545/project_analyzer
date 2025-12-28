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

# Update
try:
    with engine.connect() as conn:
        # Update repo_detail
        detail_prompt = "请阅读以下项目 README 内容，详细说明这个项目是干什么的，核心功能有哪些。请务必使用中文回答，并使用 Markdown 格式。内容：\n\n{content}"
        result = conn.execute(text("UPDATE prompt_config SET content=:c WHERE scene='repo_detail'"), {"c": detail_prompt})
        print(f"Updated repo_detail: {result.rowcount} rows")
        
        # Update repo_summary
        summary_prompt = "请根据以下项目详细介绍，将其汇总为50字以内的纯文本简述（中文）：\n\n{detail}"
        result = conn.execute(text("UPDATE prompt_config SET content=:c WHERE scene='repo_summary'"), {"c": summary_prompt})
        print(f"Updated repo_summary: {result.rowcount} rows")
        
        conn.commit()
        print("Prompts updated successfully.")
except Exception as e:
    print(f"Error updating prompts: {e}")
