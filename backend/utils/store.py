import os
import json

# Determine Base Dir
# Docker: /app/utils/.. -> /app
# Local: backend/utils/.. -> backend
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Determine Data Dir
# Local: backend/../data -> backend/data (Wrong if data is at root)
# But let's check if ../data exists relative to backend
if os.path.exists(os.path.join(BASE_DIR, '..', 'data')):
    DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'data'))
else:
    DATA_DIR = os.path.join(BASE_DIR, 'data')

# Determine Logs Dir
if os.path.exists(os.path.join(BASE_DIR, '..', 'logs')):
    LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'logs'))
else:
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Determine Articles Dir
if os.path.exists(os.path.join(BASE_DIR, '..', 'articles')):
    ARTICLES_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'articles'))
else:
    ARTICLES_DIR = os.path.join(BASE_DIR, 'articles')

CONFIG_DIR = os.path.join(DATA_DIR, 'configs')
REPOS_BASE_DIR = os.path.join(DATA_DIR, 'repos')
RECORDS_FILE_PULL = os.path.join(DATA_DIR, 'pull_records.json')
RECORDS_FILE_PUBLISH = os.path.join(DATA_DIR, 'publish_history.json')
LINKS_FILE_PUBLISH = os.path.join(DATA_DIR, 'publish_links.json')
TASKS_FILE_MAKE = os.path.join(DATA_DIR, 'make_tasks.json')

os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


def read_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default


def write_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
