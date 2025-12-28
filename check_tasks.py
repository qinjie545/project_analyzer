import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils.db import session_scope, MakeTask, init_engine

def check_tasks():
    init_engine()
    with session_scope() as db:
        try:
            tasks = db.query(MakeTask).all()
            print(f"Found {len(tasks)} tasks:")
            for task in tasks:
                print(f"ID: {task.id}, Repo: {task.repo_name}, Status: {task.status}, Created: {task.created_at}, Updated: {task.updated_at}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_tasks()
