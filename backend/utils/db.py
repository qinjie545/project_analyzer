import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, JSON, Time, Enum, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
_engine = None
_SessionLocal = None


def _make_db_url() -> Optional[str]:
    host = os.getenv('MYSQL_HOST')
    user = os.getenv('MYSQL_USER')
    password = os.getenv('MYSQL_PASSWORD')
    database = os.getenv('MYSQL_DATABASE', 'github_daily_report')
    port = os.getenv('MYSQL_PORT', '3306')
    if host and user and password:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    return None


def init_engine(echo: bool = False, override_url: Optional[str] = None):
    global _engine, _SessionLocal
    url = override_url or _make_db_url()
    if not url:
        return None
    _engine = create_engine(url, echo=echo, pool_pre_ping=True, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    return _engine


def get_engine():
    return _engine


@contextmanager
def session_scope():
    if _SessionLocal is None:
        yield None
        return
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Models (subset for initial implementation)
class PullConfig(Base):
    __tablename__ = 'pull_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sources = Column(JSON)
    keywords = Column(String(1024))
    keywords_list = Column(JSON)
    rule = Column(String(64))
    frequency = Column(String(16))  # 'daily' | 'weekly'
    weekday = Column(Integer)
    times_per_week = Column(Integer)
    start_time = Column(Time)
    concurrency = Column(Integer)
    per_project_delay = Column(Integer)
    batch = Column(Integer)
    updated_at = Column(DateTime)


class PullRecord(Base):
    __tablename__ = 'pull_record'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(64))
    repo_full_name = Column(String(255))
    url = Column(String(512))
    pull_time = Column(DateTime)
    stars = Column(Integer)
    forks = Column(Integer)
    save_path = Column(String(512))
    result_status = Column(String(32))
    rule = Column(String(64))
    summary = Column(Text)
    detail = Column(Text)
    token_count = Column(Integer, default=0)


class MakeTask(Base):
    __tablename__ = 'make_task'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(String(64), unique=True)
    input_ref = Column(String(512))
    repo_name = Column(String(255))
    article_type = Column(String(64))
    content = Column(Text)
    detailed_content = Column(Text)
    thinking_content = Column(Text)
    feedback = Column(Text)
    status = Column(String(32))
    log_file = Column(String(512))
    created_at = Column(DateTime)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)


class PublishHistory(Base):
    __tablename__ = 'publish_history'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255))
    platform = Column(String(64))
    time = Column(DateTime)
    status = Column(String(32))
    url = Column(String(512))


class MakeConfig(Base):
    __tablename__ = 'make_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provider = Column(String(64))
    base_url = Column(String(255))
    model = Column(String(128))
    external_api_key = Column(String(4096))
    engine_version = Column(String(16), default='v1')
    word_limit = Column(Integer, default=8000)
    updated_at = Column(DateTime)


class PublishConfig(Base):
    __tablename__ = 'publish_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platforms = Column(JSON)
    account = Column(String(128))
    api_key = Column(String(4096))
    publish_time = Column(Time)
    updated_at = Column(DateTime)


class PromptConfig(Base):
    __tablename__ = 'prompt_config'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scene = Column(String(64))  # Removed unique constraint logic in code, DB migration might be needed manually if strict
    name = Column(String(128))
    content = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
