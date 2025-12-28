#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 服务器
为前端提供 GitHub 项目数据接口
"""

import os
import json
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import datetime
from typing import List, Dict, Optional

try:
    from utils.token_counter import count_tokens_in_dir
    from utils.text_utils import sanitize_mermaid_content
except ImportError:
    try:
        from utils.token_counter import count_tokens_in_dir
        from utils.text_utils import sanitize_mermaid_content
    except ImportError:
        count_tokens_in_dir = lambda x: 0
        sanitize_mermaid_content = lambda x: x


import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化数据库引擎（若未提供 MYSQL_* 则不启用 DB）
try:
    from .utils.db import init_engine, session_scope, PullConfig as DBPullConfig, PullRecord as DBPullRecord, MakeTask as DBMakeTask, PublishHistory as DBPublishHistory, MakeConfig as DBMakeConfig, PublishConfig as DBPublishConfig, PromptConfig as DBPromptConfig
    init_engine()
except Exception:
    try:
        from utils.db import init_engine, session_scope, PullConfig as DBPullConfig, PullRecord as DBPullRecord, MakeTask as DBMakeTask, PublishHistory as DBPublishHistory, MakeConfig as DBMakeConfig, PublishConfig as DBPublishConfig, PromptConfig as DBPromptConfig
        init_engine()
    except Exception as e:
        print(f"DB Import/Init Failed (2nd attempt): {e}")
        session_scope = None
        DBPullConfig = DBPullRecord = DBMakeTask = DBPublishHistory = DBPromptConfig = None


# Auto-migration for new columns
if session_scope:
    try:
        from sqlalchemy import text
        # Try to import get_engine and Base
        try:
            from .utils.db import get_engine, Base
        except ImportError:
            from utils.db import get_engine, Base
            
        engine = get_engine()
        if engine:
            # Ensure all tables exist (including new PromptConfig)
            Base.metadata.create_all(engine)
            
            with engine.connect() as conn:
                # Check and add summary
                try:
                    conn.execute(text("SELECT summary FROM pull_record LIMIT 1"))
                except Exception:
                    conn.execute(text("ALTER TABLE pull_record ADD COLUMN summary TEXT"))
                    print("Migrated: Added summary column")
                
                # Check and add detail
                try:
                    conn.execute(text("SELECT detail FROM pull_record LIMIT 1"))
                    # Upgrade to LONGTEXT
                    try:
                        conn.execute(text("ALTER TABLE pull_record MODIFY detail LONGTEXT"))
                    except Exception as e:
                        print(f"Modify detail to LONGTEXT failed: {e}")
                except Exception:
                    conn.execute(text("ALTER TABLE pull_record ADD COLUMN detail LONGTEXT"))
                    print("Migrated: Added detail column")
                
                # Drop unique index on prompt_config (moved here for safer DDL)
                try:
                    conn.execute(text("DROP INDEX scene ON prompt_config"))
                    print("Migrated: Dropped unique index 'scene' on prompt_config")
                except Exception as e:
                    # Ignore "Can't DROP 'scene'; check that column/key exists"
                    if "1091" not in str(e):
                        print(f"Drop index 'scene' failed: {e}")

                conn.commit()
                
            # Initialize default prompts
            if DBPromptConfig:
                try:
                    from sqlalchemy import select, text
                    with session_scope() as s:
                        # 1. Check and add columns if missing
                        try:
                            s.execute(text("SELECT name FROM prompt_config LIMIT 1"))
                        except Exception:
                            try:
                                s.execute(text("ALTER TABLE prompt_config ADD COLUMN name VARCHAR(128)"))
                                print("Migrated: Added name column to prompt_config")
                            except Exception as e:
                                print(f"Failed to add name column: {e}")

                        try:
                            s.execute(text("SELECT is_default FROM prompt_config LIMIT 1"))
                        except Exception:
                            try:
                                s.execute(text("ALTER TABLE prompt_config ADD COLUMN is_default BOOLEAN DEFAULT 0"))
                                print("Migrated: Added is_default column to prompt_config")
                            except Exception as e:
                                print(f"Failed to add is_default column: {e}")
                        
                        # 2. Drop unique index on scene if exists (MySQL specific attempt)
                        # Moved to engine connection block above
                        pass

                        s.commit()

                        # 3. Initialize Templates
                        # 3.1 Article Generation Templates
                        wechat_scene = "article_generation"
                        existing_wechat = s.execute(select(DBPromptConfig).filter_by(scene=wechat_scene)).scalars().all()
                        
                        if not existing_wechat:
                            templates = [
                                {
                                    "name": "微信公众号爆款风",
                                    "is_default": True,
                                    "content": """你是一个专业的微信公众号文章编辑。请根据提供的GitHub项目信息，撰写一篇吸引人的公众号文章。

要求：
1. 标题要吸引人，使用“爆款”标题风格，例如“惊了！...”、“GitHub霸榜...”等。
2. 内容包含项目介绍、核心功能、使用场景、部署方式等。
3. 语言通俗易懂，排版美观（使用Markdown）。
4. 适当使用Emoji表情 🚀 🔥。
5. 字数在1000字左右。
6. 结尾引导关注。
7. 必须做到逻辑严谨，语义通顺，符合事实。
8. 保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。"""
                                },
                                {
                                    "name": "技术硬核风",
                                    "is_default": False,
                                    "content": """你是一个资深技术专家。请对提供的GitHub项目进行深度技术解读。

要求：
1. 标题专业，直接点明技术核心。
2. 深入分析架构、代码实现原理、技术难点。
3. 对比同类技术方案的优劣。
4. 给出具体的代码示例或配置片段。
5. 适合中高级开发者阅读。
6. 必须做到逻辑严谨，语义通顺，符合事实。
7. 保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。"""
                                },
                                {
                                    "name": "简报资讯风",
                                    "is_default": False,
                                    "content": """你是一个科技资讯编辑。请快速播报这个GitHub项目。

要求：
1. 标题简洁明了。
2. 用300字以内概括项目核心价值。
3. 列出3个主要亮点。
4. 适合快速阅读。
5. 必须做到逻辑严谨，语义通顺，符合事实。
6. 保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。"""
                                }
                            ]
                            
                            for t in templates:
                                s.add(DBPromptConfig(
                                    scene=wechat_scene,
                                    name=t["name"],
                                    content=t["content"],
                                    is_default=t["is_default"],
                                    created_at=datetime.now(),
                                    updated_at=datetime.now()
                                ))
                            print(f"Initialized {len(templates)} templates for {wechat_scene}")

                        # 3.2 Repo Detail Template
                        detail_scene = "repo_detail"
                        existing_detail = s.execute(select(DBPromptConfig).filter_by(scene=detail_scene)).scalars().first()
                        if not existing_detail:
                            s.add(DBPromptConfig(
                                scene=detail_scene,
                                name="默认详情解析",
                                content="请阅读以下项目 README 内容，详细说明这个项目是干什么的，核心功能有哪些。请务必使用中文回答，并使用 Markdown 格式。如果 README 是英文的，请将其中的核心内容翻译成中文。回答必须逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。内容：\n\n{content}",
                                is_default=True,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            ))
                            print(f"Initialized template for {detail_scene}")

                        # 3.3 Repo Summary Template
                        summary_scene = "repo_summary"
                        existing_summary = s.execute(select(DBPromptConfig).filter_by(scene=summary_scene)).scalars().first()
                        if not existing_summary:
                            s.add(DBPromptConfig(
                                scene=summary_scene,
                                name="默认简述生成",
                                content="请根据以下项目详细介绍，将其汇总为50字以内的纯文本简述（中文）。确保回答完全是中文，且逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实：\n\n{detail}",
                                is_default=True,
                                created_at=datetime.now(),
                                updated_at=datetime.now()
                            ))
                            print(f"Initialized template for {summary_scene}")

                        s.commit()
                            
                except Exception as e:
                    print(f"Prompt init failed: {e}")

                # Check and add columns to make_task
                try:
                    with engine.connect() as conn:
                        try:
                            conn.execute(text("SELECT content FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN content LONGTEXT"))
                            print("Migrated: Added content column to make_task")
                        
                        try:
                            conn.execute(text("SELECT repo_name FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN repo_name VARCHAR(255)"))
                            print("Migrated: Added repo_name column to make_task")

                        try:
                            conn.execute(text("SELECT article_type FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN article_type VARCHAR(64)"))
                            print("Migrated: Added article_type column to make_task")

                        try:
                            conn.execute(text("SELECT log_file FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN log_file VARCHAR(512)"))
                            print("Migrated: Added log_file column to make_task")

                        try:
                            conn.execute(text("SELECT feedback FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN feedback LONGTEXT"))
                            print("Migrated: Added feedback column to make_task")

                        try:
                            conn.execute(text("SELECT detailed_content FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN detailed_content LONGTEXT"))
                            print("Migrated: Added detailed_content column to make_task")

                        try:
                            conn.execute(text("SELECT thinking_content FROM make_task LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_task ADD COLUMN thinking_content LONGTEXT"))
                            print("Migrated: Added thinking_content column to make_task")
                        
                        # Check and add engine_version to make_config
                        try:
                            conn.execute(text("SELECT engine_version FROM make_config LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_config ADD COLUMN engine_version VARCHAR(16) DEFAULT 'v1'"))
                            print("Migrated: Added engine_version column to make_config")

                        # Check and add word_limit to make_config
                        try:
                            conn.execute(text("SELECT word_limit FROM make_config LIMIT 1"))
                        except Exception:
                            conn.execute(text("ALTER TABLE make_config ADD COLUMN word_limit INT DEFAULT 8000"))
                            print("Migrated: Added word_limit column to make_config")

                        # Backfill repo_name if missing
                        try:
                            # Use explicit collation to avoid mix error
                            conn.execute(text("""
                                UPDATE make_task m
                                JOIN pull_record p ON m.input_ref COLLATE utf8mb4_unicode_ci = CAST(p.id AS CHAR) COLLATE utf8mb4_unicode_ci
                                SET m.repo_name = p.repo_full_name
                                WHERE m.repo_name IS NULL OR m.repo_name = ''
                            """))
                            print("Migrated: Backfilled repo_name in make_task")
                        except Exception as e:
                            # Try fallback if collation fails (e.g. if DB uses different collation)
                            try:
                                conn.execute(text("""
                                    UPDATE make_task m
                                    JOIN pull_record p ON m.input_ref = CAST(p.id AS CHAR)
                                    SET m.repo_name = p.repo_full_name
                                    WHERE m.repo_name IS NULL OR m.repo_name = ''
                                """))
                            except Exception as e2:
                                print(f"Backfill repo_name failed: {e}")

                        conn.commit()
                except Exception as e:
                    print(f"MakeTask migration failed: {e}")

    except Exception as e:
        print(f"Migration check failed: {e}")


def get_latest_data() -> Optional[Dict]:
    """
    获取最新的项目数据
    
    Returns:
        项目数据字典
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        return None
    
    # 查找最新的数据文件
    files = [f for f in os.listdir(data_dir) if f.startswith('repos_') and f.endswith('.json')]
    if not files:
        return None
    
    files.sort(reverse=True)
    latest_file = os.path.join(data_dir, files[0])
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/api/repos', methods=['GET'])
def get_repos():
    """获取项目列表"""
    data = get_latest_data() or {}
    return jsonify({
        'success': True,
        'message': '获取成功',
        'data': data.get('repos', []),
        'fetch_date': data.get('fetch_date')
    })


@app.route('/api/repos/<int:limit>', methods=['GET'])
def get_repos_limit(limit):
    """获取指定数量的项目列表"""
    data = get_latest_data()
    if not data:
        return jsonify({
            'success': False,
            'message': '暂无数据',
            'data': []
        }), 404
    
    repos = data.get('repos', [])[:limit]
    return jsonify({
        'success': True,
        'message': '获取成功',
        'data': repos,
        'fetch_date': data.get('fetch_date')
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    data = get_latest_data() or {}
    repos = data.get('repos', [])

    # 统计语言分布
    language_stats = {}
    total_stars = 0
    total_forks = 0

    for repo in repos:
        lang = repo.get('language', 'Unknown')
        language_stats[lang] = language_stats.get(lang, 0) + 1
        total_stars += repo.get('stars', 0)
        total_forks += repo.get('forks', 0)

    return jsonify({
        'success': True,
        'message': '获取成功',
        'data': {
            'total_repos': len(repos),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'language_distribution': language_stats,
            'fetch_date': data.get('fetch_date')
        }
    })


@app.route('/api/article/tasks/pending_review', methods=['GET'])
def get_pending_review_tasks():
    """获取待审核的文章任务"""
    if not session_scope or not DBMakeTask:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    try:
        from sqlalchemy import select, desc
        with session_scope() as s:
            # 假设 status='generated' 表示待审核
            rows = s.execute(select(DBMakeTask).filter_by(status='generated').order_by(desc(DBMakeTask.created_at))).scalars().all()
            data = []
            for r in rows:
                data.append({
                    'id': r.id,
                    'repo_name': r.repo_name,
                    'article_type': r.article_type,
                    'status': r.status,
                    'content': r.content,
                    'detailed_content': r.detailed_content,
                    'thinking_content': r.thinking_content,
                    'feedback': r.feedback,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                })
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/article/audit', methods=['POST'])
def audit_article():
    """审核文章"""
    if not session_scope or not DBMakeTask:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    data = request.get_json(silent=True) or {}
    task_id = data.get('id')
    action = data.get('action') # 'approve' or 'reject'
    content = data.get('content') # 修改后的内容
    opinion = data.get('opinion') # 审批意见
    
    if not task_id or not action:
        return jsonify({'success': False, 'message': 'Missing id or action'}), 400
        
    try:
        with session_scope() as s:
            task = s.get(DBMakeTask, task_id)
            if not task:
                return jsonify({'success': False, 'message': 'Task not found'}), 404
                
            if action == 'approve':
                task.status = 'approved'
                task.content = sanitize_mermaid_content(content) # 保存修改后的内容
                # Generate files
                try:
                    from utils.file_generator import generate_files
                    output_dir = os.path.join(os.path.dirname(__file__), 'data', 'generated_docs')
                    title = task.repo_name or f"Article_{task.task_id}"
                    generate_files(task.task_id, title, content, output_dir)
                except Exception as e:
                    print(f"File generation failed: {e}")
                    # Log error but don't fail the approval?
                    # Or maybe fail? Let's log.
                    with open(os.path.join(LOGS_DIR, 'article_audit.log'), 'a', encoding='utf-8') as lf:
                        lf.write(f"{datetime.now().isoformat()} File generation failed for {task_id}: {e}\n")

            elif action == 'reject':
                task.status = 'pending' # 回入任务池
            elif action == 'revise':
                task.status = 'queued'
                task.feedback = opinion
                # Trigger re-processing
                import threading
                t = threading.Thread(target=_process_article_task, args=(task.task_id, task.input_ref))
                t.start()
            
            print(f"Audit task {task_id}: {action}, opinion: {opinion}")
            
            s.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'message': 'API 服务正常运行',
        'timestamp': datetime.now().isoformat()
    })

# MCP + LangChain 分析入口（占位实现）
@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        from analysis.mcp_agent import analyze_github_repo
    except ImportError:
        from .analysis.mcp_agent import analyze_github_repo
        
    data = request.get_json(silent=True) or {}
    full_name = data.get('repo_full_name')
    api_key = data.get('external_api_key')  # 前端可选传入，用于外部模型
    provider = data.get('model_provider')
    base_url = data.get('model_base_url')
    model = data.get('model_name')
    if not full_name:
        return jsonify({
            'success': False,
            'message': '缺少 repo_full_name'
        }), 400
    try:
        result = analyze_github_repo(full_name, api_key=api_key, provider=provider, base_url=base_url, model=model)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 文章预审接口
@app.route('/api/article/latest', methods=['GET'])
def get_latest_article():
    articles_dir = ARTICLES_DIR
    if not os.path.exists(articles_dir):
        return jsonify({'success': True, 'data': {'file': None, 'content': ''}})
    files = sorted([f for f in os.listdir(articles_dir) if f.endswith('.md')], reverse=True)
    if not files:
        return jsonify({'success': True, 'data': {'file': None, 'content': ''}})
    latest = os.path.join(articles_dir, files[0])
    with open(latest, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'success': True, 'data': {'file': files[0], 'content': content}})

@app.route('/api/article/save', methods=['POST'])
def save_article():
    data = request.get_json(silent=True) or {}
    content = data.get('content')
    if not content:
        return jsonify({'success': False, 'message': '缺少 content'}), 400
    articles_dir = ARTICLES_DIR
    os.makedirs(articles_dir, exist_ok=True)
    # 保存到最新文件名（若存在），否则创建新文件
    files = sorted([f for f in os.listdir(articles_dir) if f.endswith('.md')], reverse=True)
    target = os.path.join(articles_dir, files[0] if files else f'preview_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(content)
    return jsonify({'success': True, 'data': {'file': os.path.basename(target)}})

@app.route('/api/article/regenerate', methods=['POST'])
def regenerate_article():
    data = request.get_json(silent=True) or {}
    suggestions = data.get('suggestions', '')
    # 占位：记录建议并返回队列状态（真实实现应调用生成脚本）
    with open(os.path.join(LOGS_DIR, 'regenerate.log'), 'a', encoding='utf-8') as lf:
        lf.write(f"{datetime.now().isoformat()} suggestions: {suggestions}\n")
    return jsonify({'success': True, 'data': {'status': 'queued'}})

# 提供默认 favicon，避免 404
@app.route('/favicon.ico')
def favicon():
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    icon_path = os.path.join(static_dir, 'favicon.ico')
    if os.path.exists(icon_path):
        return send_from_directory(static_dir, 'favicon.ico')
    return ('', 204)

# ========= 辅助：简单配置与记录持久化 =========
try:
    from .utils.store import CONFIG_DIR, LOGS_DIR, ARTICLES_DIR, RECORDS_FILE_PULL, RECORDS_FILE_PUBLISH, LINKS_FILE_PUBLISH, TASKS_FILE_MAKE, read_json as _read_json, write_json as _write_json
except ImportError:
    # Fallback when running without package context
    from utils.store import CONFIG_DIR, LOGS_DIR, ARTICLES_DIR, RECORDS_FILE_PULL, RECORDS_FILE_PUBLISH, LINKS_FILE_PUBLISH, TASKS_FILE_MAKE, read_json as _read_json, write_json as _write_json


# ========= 抓取（Pull/Fetch）API =========
@app.route('/api/pull/config', methods=['GET', 'POST'])
def pull_config():
    cfg_path = os.path.join(CONFIG_DIR, 'pull_config.json')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        # 基本字段白名单，避免脏数据
        allow = {
            'sources', 'keywords', 'rule',
            'frequency', 'weekday', 'timesPerWeek', 'startTime',
            'concurrency', 'perProjectDelay', 'batch'
        }
        saved = {k: data.get(k) for k in allow}
        # 关键字：支持英文逗号分隔
        raw_kw = (saved.get('keywords') or '')
        if isinstance(raw_kw, str):
            kw_list = [s.strip() for s in raw_kw.split(',') if s.strip()]
        elif isinstance(raw_kw, list):
            kw_list = [str(s).strip() for s in raw_kw if str(s).strip()]
            saved['keywords'] = ', '.join(kw_list)
        else:
            kw_list = []
        saved['keywords_list'] = kw_list
        saved['updated_at'] = datetime.now().isoformat()
        # JSON 持久化
        _write_json(cfg_path, saved)
        # DB 持久化（若可用）
        if session_scope and DBPullConfig:
            try:
                from datetime import time
                st = None
                start_time = saved.get('startTime')
                if isinstance(start_time, str) and len(start_time) >= 4:
                    hh, mm = start_time.split(':')[0:2]
                    st = time(int(hh), int(mm))
                with session_scope() as s:
                    obj = DBPullConfig(
                        sources=saved.get('sources'),
                        keywords=saved.get('keywords'),
                        keywords_list=saved.get('keywords_list'),
                        rule=saved.get('rule'),
                        frequency=saved.get('frequency'),
                        weekday=saved.get('weekday'),
                        times_per_week=saved.get('timesPerWeek'),
                        start_time=st,
                        concurrency=saved.get('concurrency'),
                        per_project_delay=saved.get('perProjectDelay'),
                        batch=saved.get('batch'),
                        updated_at=datetime.now()
                    )
                    s.add(obj)
            except Exception:
                pass
        return jsonify({'success': True, 'data': saved})
    else:
        # 优先从 DB 获取最新
        if session_scope and DBPullConfig:
            try:
                from sqlalchemy import select, desc
                with session_scope() as s:
                    row = s.execute(select(DBPullConfig).order_by(desc(DBPullConfig.updated_at))).scalars().first()
                    if row:
                        data = {
                            'sources': row.sources,
                            'keywords': row.keywords,
                            'keywords_list': row.keywords_list,
                            'rule': row.rule,
                            'frequency': row.frequency,
                            'weekday': row.weekday,
                            'timesPerWeek': row.times_per_week,
                            'startTime': row.start_time.strftime('%H:%M') if row.start_time else None,
                            'concurrency': row.concurrency,
                            'perProjectDelay': row.per_project_delay,
                            'batch': row.batch,
                            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                        }
                        # Ensure keywords string is always available
                        if (not data.get('keywords')) and isinstance(data.get('keywords_list'), list):
                            data['keywords'] = ', '.join([str(s).strip() for s in data['keywords_list'] if str(s).strip()])
                        return jsonify({'success': True, 'data': data})
            except Exception:
                pass
        data = _read_json(cfg_path, {}) or {}
        # Ensure keywords present when only keywords_list exists
        if (not data.get('keywords')) and isinstance(data.get('keywords_list'), list):
            data['keywords'] = ', '.join([str(s).strip() for s in data['keywords_list'] if str(s).strip()])
        return jsonify({'success': True, 'data': data})


import threading
from pull.github_pull import search_github_repos, clone_repository, generate_summary, get_readme_content
from utils.store import DATA_DIR

def _call_llm_service(provider, base_url, api_key, model_name, messages, max_tokens=2000):
    """Helper to call LLM service using LangChain."""
    try:
        from llm.langchain_utils import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        llm = get_llm(provider, api_key, base_url, model_name)
        # Bind max_tokens for this call
        llm = llm.bind(max_tokens=max_tokens)

        lc_messages = []
        for m in messages:
            if m['role'] == 'system':
                lc_messages.append(SystemMessage(content=m['content']))
            elif m['role'] == 'user':
                lc_messages.append(HumanMessage(content=m['content']))
            elif m['role'] == 'assistant':
                lc_messages.append(AIMessage(content=m['content']))
        
        response = llm.invoke(lc_messages)
        return response.content
    except Exception as e:
        print(f"LLM Call Error (LangChain): {e}")
        return None


def get_prompt(scene, default_content):
    """Get prompt from DB (prefer default) or use default and save."""
    if not session_scope or not DBPromptConfig:
        return default_content
        
    try:
        from sqlalchemy import select, desc
        with session_scope() as s:
            # Try to find default for this scene
            row = s.execute(select(DBPromptConfig).filter_by(scene=scene, is_default=True)).scalars().first()
            if row:
                return row.content
            
            # Try any for this scene
            row = s.execute(select(DBPromptConfig).filter_by(scene=scene)).scalars().first()
            if row:
                return row.content
            
            # Insert default
            new_prompt = DBPromptConfig(
                scene=scene, 
                name="默认模板",
                content=default_content,
                is_default=True
            )
            s.add(new_prompt)
            return default_content
    except Exception as e:
        print(f"Get Prompt Error: {e}")
        return default_content


@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """Get all prompts grouped by scene."""
    if not session_scope or not DBPromptConfig:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    try:
        from sqlalchemy import select, desc
        with session_scope() as s:
            rows = s.execute(select(DBPromptConfig).order_by(DBPromptConfig.scene, DBPromptConfig.id)).scalars().all()
            data = []
            for r in rows:
                data.append({
                    'id': r.id,
                    'scene': r.scene,
                    'name': r.name or '未命名',
                    'content': r.content,
                    'is_default': r.is_default,
                    'updated_at': r.updated_at.isoformat() if r.updated_at else None
                })
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/prompts', methods=['POST'])
def save_prompt():
    """Create or update a prompt."""
    if not session_scope or not DBPromptConfig:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    data = request.get_json(silent=True) or {}
    p_id = data.get('id')
    scene = data.get('scene')
    name = data.get('name')
    content = data.get('content')
    
    if not scene or not content:
        return jsonify({'success': False, 'message': 'Missing scene or content'}), 400
        
    try:
        with session_scope() as s:
            if p_id:
                # Update
                obj = s.get(DBPromptConfig, p_id)
                if obj:
                    obj.name = name
                    obj.content = content
                    obj.updated_at = datetime.now()
            else:
                # Create
                # Check if it's the first one, make it default
                from sqlalchemy import select
                count = s.execute(select(DBPromptConfig).filter_by(scene=scene)).scalars().all()
                is_default = len(count) == 0
                
                obj = DBPromptConfig(
                    scene=scene,
                    name=name,
                    content=content,
                    is_default=is_default,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                s.add(obj)
            s.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/prompts/default', methods=['POST'])
def set_default_prompt():
    """Set a prompt as default for its scene."""
    if not session_scope or not DBPromptConfig:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    data = request.get_json(silent=True) or {}
    p_id = data.get('id')
    
    if not p_id:
        return jsonify({'success': False, 'message': 'Missing id'}), 400
        
    try:
        with session_scope() as s:
            target = s.get(DBPromptConfig, p_id)
            if not target:
                return jsonify({'success': False, 'message': 'Prompt not found'}), 404
                
            # Unset others in same scene
            from sqlalchemy import update
            s.execute(
                update(DBPromptConfig)
                .where(DBPromptConfig.scene == target.scene)
                .values(is_default=False)
            )
            
            # Set target
            target.is_default = True
            s.commit()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def _generate_ai_summary_detail(repo_dir):
    """Generate summary and detail using configured LLM."""
    from pull.github_pull import get_readme_content, generate_summary
    content = get_readme_content(repo_dir)
    if not content:
        return "暂无介绍", "暂无 README 内容"

    # Get Config
    provider = 'openai'
    base_url = ''
    model_name = ''
    api_key = ''
    
    # Try DB
    if session_scope and DBMakeConfig:
        try:
            from sqlalchemy import select, desc
            with session_scope() as s:
                row = s.execute(select(DBMakeConfig).order_by(desc(DBMakeConfig.updated_at))).scalars().first()
                if row:
                    provider = row.provider
                    base_url = row.base_url
                    model_name = row.model
                    api_key = row.external_api_key
        except Exception:
            pass
            
    # Try JSON
    if not api_key:
        cfg = _read_json(os.path.join(CONFIG_DIR, 'model_config.json'), {})
        provider = cfg.get('provider', 'openai')
        base_url = cfg.get('base_url', '')
        model_name = cfg.get('model', '')
        api_key = cfg.get('external_api_key', '')

    # Ensure api_key is string
    if isinstance(api_key, bytes):
        api_key = api_key.decode('utf-8')

    if not api_key:
        return generate_summary(repo_dir), content

    # 1. Generate Detail
    default_detail_tmpl = "请阅读以下项目 README 内容，详细说明这个项目是干什么的，核心功能有哪些。请务必使用中文回答，并使用 Markdown 格式。如果 README 是英文的，请将其中的核心内容翻译成中文。回答必须逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。内容：\n\n{content}"
    detail_tmpl = get_prompt('repo_detail', default_detail_tmpl)
    
    # Ensure content is string
    if content is None: content = ""
    
    # Limit content length to avoid token overflow, but keep template intact
    # We assume template has {content} placeholder
    try:
        detail_prompt = detail_tmpl.format(content=content[:10000])
    except Exception:
        detail_prompt = f"请阅读以下项目 README 内容，详细说明这个项目是干什么的，核心功能有哪些。请务必使用中文回答，并使用 Markdown 格式。如果 README 是英文的，请将其中的核心内容翻译成中文。回答必须逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实。内容：\n\n{content[:10000]}"

    print(f"DEBUG: Generating detail with prompt: {detail_prompt[:200]}...")
    print(f"DEBUG: Using provider={provider}, model={model_name}, base_url={base_url}, key={api_key[:4]}***{api_key[-4:] if len(api_key)>4 else ''}")
    
    # Add system prompt for Chinese enforcement
    messages = [
        {"role": "system", "content": "You are an expert software analyst. You must answer in Chinese. If the input content is in English or another language, translate the key information into Chinese. Ensure all large blocks of text are in Chinese. Your response must be logically rigorous, semantically smooth, and factually accurate. Maintain a professional perspective, do not exaggerate. Be realistic and rigorous. Avoid words like 'extremely high', 'huge', 'perfect', etc. unless strictly proven. Focus on technical facts."},
        {"role": "user", "content": detail_prompt}
    ]
    detail = _call_llm_service(provider, base_url, api_key, model_name, messages)
    print(f"DEBUG: Received detail: {str(detail)[:200]}...")
    
    if not detail:
        detail = content  # Fallback

    # Ensure detail is string
    if detail is None: detail = ""

    # 2. Generate Summary
    default_summary_tmpl = "请根据以下项目详细介绍，将其汇总为50字以内的纯文本简述（中文）。确保回答完全是中文，且逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实：\n\n{detail}"
    summary_tmpl = get_prompt('repo_summary', default_summary_tmpl)
    try:
        summary_prompt = summary_tmpl.format(detail=detail[:5000])
    except Exception:
        summary_prompt = f"请根据以下项目详细介绍，将其汇总为50字以内的纯文本简述（中文）。确保回答完全是中文，且逻辑严谨，语义通顺，符合事实。保持专业视角，不要过大夸张，要做到求实严谨。避免使用“极高”、“极大”、“完美”等夸张词汇，专注于技术事实：\n\n{detail[:5000]}"

    print(f"DEBUG: Generating summary with prompt: {summary_prompt[:200]}...")
    messages_summary = [
        {"role": "system", "content": "You are an expert software analyst. You must answer in Chinese. Your response must be logically rigorous, semantically smooth, and factually accurate. Maintain a professional perspective, do not exaggerate. Be realistic and rigorous. Avoid words like 'extremely high', 'huge', 'perfect', etc. unless strictly proven. Focus on technical facts."},
        {"role": "user", "content": summary_prompt}
    ]
    summary = _call_llm_service(provider, base_url, api_key, model_name, messages_summary)
    print(f"DEBUG: Received summary: {str(summary)[:200]}...")
    
    if not summary:
        summary = generate_summary(repo_dir) # Fallback

    return summary, detail


def _background_clone(items, concurrency=1, delay=0):
    """Background task to clone repos and update status."""
    logger.info(f"Starting background clone for {len(items)} items with concurrency={concurrency}, delay={delay}")
    
    # Update JSON status helper
    import threading
    json_lock = threading.Lock()
    
    def update_json_status(url, status, summary=None, detail=None, token_count=0):
        try:
            with json_lock:
                records = _read_json(RECORDS_FILE_PULL, [])
                updated = False
                for r in records:
                    if r.get('url') == url:
                        r['status'] = status
                        if summary: r['summary'] = summary
                        if detail: r['detail'] = detail
                        if token_count > 0: r['token_count'] = token_count
                        updated = True
                        break
                if updated:
                    _write_json(RECORDS_FILE_PULL, records)
        except Exception as e:
            logger.error(f"JSON update failed: {e}")
            pass

    def process_item(item):
        url = item.get('url')
        path = item.get('path')
        if not url or not path:
            return
        
        if delay > 0:
            time.sleep(delay)
        
        logger.info(f"Cloning {url} to {path}")
        # Execute Clone
        success = clone_repository(url, path)
        status = 'cloned' if success else 'failed'
        logger.info(f"Clone result for {url}: {status}")
        
        # Calculate Tokens
        token_count = 0
        if success:
            try:
                token_count = count_tokens_in_dir(path)
                logger.info(f"Token count for {url}: {token_count}")
            except Exception as e:
                logger.error(f"Token count failed: {e}")
                pass
        
        # Generate Summary & Detail if cloned
        summary = None
        detail = None
        if success:
            try:
                logger.info(f"Generating summary for {url}")
                summary, detail = _generate_ai_summary_detail(path)
                logger.info(f"Summary generated for {url}")
            except Exception as e:
                logger.error(f"Summary Gen Error: {e}")
                pass
        
        # Update DB
        if session_scope and DBPullRecord:
            try:
                with session_scope() as s:
                    from sqlalchemy import select, desc
                    rec = s.execute(
                        select(DBPullRecord)
                        .filter_by(url=url, result_status='pending')
                        .order_by(desc(DBPullRecord.pull_time))
                    ).scalars().first()
                    if rec:
                        rec.result_status = status
                        rec.token_count = token_count
                        if summary: rec.summary = summary
                        if detail: rec.detail = detail
                        s.commit() # Ensure commit
            except Exception as e:
                logger.error(f"DB update failed: {e}")
                pass
        
        # Update JSON
        update_json_status(url, status, summary, detail, token_count)

    if concurrency > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            executor.map(process_item, items)
    else:
        for item in items:
            process_item(item)
            
    logger.info("Background clone finished")


@app.route('/api/pull/run', methods=['POST'])
def pull_run():
    """Run a GitHub pull with given keyword and limit, clone repos and record to DB/JSON."""
    payload = request.get_json(silent=True) or {}
    logger.info(f"Received pull_run request with payload: {payload}")
    
    keyword = payload.get('keyword') or 'GPT'
    limit = int(payload.get('limit') or 10)
    sort = payload.get('sort') or 'stars'
    simulate = bool(payload.get('simulate')) or (os.getenv('FLASK_ENV') == 'test')
    concurrency = int(payload.get('concurrency') or 1)
    delay = int(payload.get('delay') or 0)
    task_id = payload.get('task_id')
    
    return _execute_pull_logic([keyword], limit, sort, simulate, task_id, concurrency, delay)


@app.route('/api/pull/run/config', methods=['POST'])
def pull_run_by_config():
    """Use latest saved pull config to run an immediate pull."""
    # 读取配置（优先 DB）
    cfg = None
    if session_scope and DBPullConfig:
        try:
            from sqlalchemy import select, desc
            with session_scope() as s:
                row = s.execute(select(DBPullConfig).order_by(desc(DBPullConfig.updated_at))).scalars().first()
                if row:
                    cfg = {
                        'keywords': row.keywords,
                        'keywords_list': row.keywords_list,
                        'rule': row.rule,
                        'batch': row.batch,
                        'concurrency': row.concurrency,
                        'perProjectDelay': row.per_project_delay,
                    }
        except Exception:
            pass
    if cfg is None:
        cfg = _read_json(os.path.join(CONFIG_DIR, 'pull_config.json'), {}) or {}
    payload = request.get_json(silent=True) or {}
    simulate = bool(payload.get('simulate')) or (os.getenv('FLASK_ENV') == 'test')
    
    # 关键字列表：前端传入的优先，其次使用最新配置
    kws = []
    raw_kw = payload.get('keywords') or cfg.get('keywords') or ''
    if isinstance(raw_kw, str) and raw_kw.strip():
        kws = [s.strip() for s in raw_kw.split(',') if s.strip()]
    else:
        # 兼容传入 keywords_list 或配置中的 keywords_list
        payload_kw_list = payload.get('keywords_list')
        if isinstance(payload_kw_list, list) and payload_kw_list:
            kws = [str(s).strip() for s in payload_kw_list if str(s).strip()]
        elif isinstance(cfg.get('keywords_list'), list) and cfg['keywords_list']:
            kws = [str(s).strip() for s in cfg['keywords_list'] if str(s).strip()]
    
    if not kws:
        kws = ['GPT'] # Default

    # 规则映射
    rule = cfg.get('rule') or 'most_stars'
    sort = 'stars'
    if rule == 'most_forks':
        sort = 'forks'
    elif rule == 'recently_updated':
        sort = 'updated'
    elif rule == 'help_wanted':
        sort = 'help-wanted-issues'
    elif rule == 'best_match':
        sort = None
    elif rule == 'trending':
        sort = 'stars'
    limit = int(cfg.get('batch') or 10)
    concurrency = int(cfg.get('concurrency') or 1)
    delay = int(cfg.get('perProjectDelay') or 0)
    
    return _execute_pull_logic(kws, limit, sort, simulate, payload.get('task_id'), concurrency, delay)


def _execute_pull_logic(keywords, limit, sort, simulate, task_id, concurrency=1, delay=0):
    logger.info(f"Executing pull logic: keywords={keywords}, limit={limit}, sort={sort}, simulate={simulate}, concurrency={concurrency}, delay={delay}")
    # keywords can be a single string or a list
    if isinstance(keywords, str):
        keywords = [keywords]
    
    token = os.getenv('GITHUB_TOKEN') or None
    from utils.store import DATA_DIR # Ensure import
    
    search_results = []
    seen_urls = set()
    now = datetime.now()
    repos_dir = os.path.join(DATA_DIR, 'repos')

    # 1. Search
    if simulate:
        owner, repo = 'octocat', 'Hello-World'
        dest = os.path.join(repos_dir, owner, repo)
        search_results = [{
            'name': f'{owner}/{repo}',
            'url': f'https://github.com/{owner}/{repo}',
            'pullTime': now,
            'stars': 100,
            'forks': 50,
            'path': dest,
            'status': 'pending'
        }]
    else:
        # Load existing URLs from DB to prevent duplicates
        existing_urls = set()
        if session_scope and DBPullRecord:
            try:
                from sqlalchemy import select
                with session_scope() as s:
                    urls = s.execute(select(DBPullRecord.url)).scalars().all()
                    existing_urls = set(urls)
                logger.info(f"Loaded {len(existing_urls)} existing URLs from DB")
            except Exception as e:
                logger.error(f"Failed to load existing URLs: {e}")

        all_items = []
        for kw in keywords:
            try:
                logger.info(f"Searching for keyword: {kw}")
                # Fetch limit items per keyword to ensure diversity
                items = search_github_repos(kw, per_page=limit, sort=sort, token=token)
                logger.info(f"Found {len(items)} items for keyword {kw}")
                for it in items:
                    url = it.get('html_url')
                    if url:
                        if url in existing_urls:
                            logger.debug(f"Skipping existing URL in DB: {url}")
                            continue
                        if url in seen_urls:
                            logger.debug(f"Skipping duplicate URL in current batch: {url}")
                            continue
                        
                        seen_urls.add(url)
                        all_items.append(it)
            except Exception as e:
                logger.error(f"Search error for {kw}: {e}")
                continue
        
        # Sort combined results if needed (though search is already sorted, mixing might mess it up)
        # If sort is stars/forks, we can resort.
        if sort == 'stars':
            all_items.sort(key=lambda x: x.get('stargazers_count', 0), reverse=True)
        elif sort == 'forks':
            all_items.sort(key=lambda x: x.get('forks_count', 0), reverse=True)
            
        # Apply global limit if desired? Or keep all unique?
        # User said "Pull M projects". Let's respect limit as total limit if it's a batch run.
        # But if we have multiple keywords, maybe we want more?
        # Let's cap at limit * len(keywords) or just limit?
        # Usually batch size is total. Let's cap at limit.
        # But if limit is small (e.g. 10) and we have 5 keywords, we get 2 per keyword?
        # Let's keep up to `limit` items total to respect the "Batch" setting.
        if len(all_items) > limit:
            all_items = all_items[:limit]

        for it in all_items:
            full_name = it.get('full_name') or f"{it.get('owner',{}).get('login','unknown')}/{it.get('name','unknown')}"
            owner = full_name.split('/')[0]
            repo = full_name.split('/')[1]
            html_url = it.get('html_url')
            stars = it.get('stargazers_count') or 0
            forks = it.get('forks_count') or 0
            dest = os.path.join(repos_dir, owner, repo)
            
            search_results.append({
                'name': full_name,
                'url': html_url,
                'pullTime': now,
                'stars': stars,
                'forks': forks,
                'path': dest,
                'status': 'pending'
            })

    # 2. Save Pending
    logger.info(f"Saving {len(search_results)} pending records")
    records = _read_json(RECORDS_FILE_PULL, [])
    from datetime import datetime as dt
    
    # Reverse to insert in correct order (though we insert at 0, so we should iterate reversed)
    for r in reversed(search_results):
        rec_json = {
            'name': r['name'],
            'url': r['url'],
            'pullTime': r['pullTime'].isoformat() if hasattr(r['pullTime'], 'isoformat') else str(r['pullTime']),
            'stars': r['stars'],
            'forks': r['forks'],
            'path': r['path'],
            'rule': sort,
            'status': 'pending'
        }
        records.insert(0, rec_json)
        if session_scope and DBPullRecord:
            try:
                with session_scope() as s:
                    s.add(DBPullRecord(
                        task_id=task_id,
                        repo_full_name=r['name'],
                        url=r['url'],
                        pull_time=r['pullTime'] if isinstance(r['pullTime'], dt) else dt.fromisoformat(r['pullTime']) if isinstance(r['pullTime'], str) else dt.now(),
                        stars=r['stars'],
                        forks=r['forks'],
                        save_path=r['path'],
                        result_status='pending',
                        rule=sort
                    ))
            except Exception as e:
                logger.error(f"DB save failed: {e}")
                pass
    _write_json(RECORDS_FILE_PULL, records)

    # 3. Background Clone
    if not simulate:
        logger.info("Starting background clone thread")
        t = threading.Thread(target=_background_clone, args=(search_results,))
        t.start()
    else:
        _background_clone(search_results)

    return jsonify({'success': True, 'data': {'count': len(search_results), 'keywords': keywords, 'sort': sort, 'status': 'started'}})


@app.route('/api/pull/test', methods=['POST'])
def pull_test():
    # legacy demo write for testing
    cfg = request.get_json(silent=True) or {}
    # keywords 支持英文逗号分隔
    raw_kw = cfg.get('keywords') or ''
    if isinstance(raw_kw, str):
        kw_list = [s.strip() for s in raw_kw.split(',') if s.strip()]
    elif isinstance(raw_kw, list):
        kw_list = [str(s).strip() for s in raw_kw if str(s).strip()]
    else:
        kw_list = []
    cfg_snapshot = dict(cfg)
    cfg_snapshot['keywords_list'] = kw_list

    # 写入一条演示记录
    records = _read_json(RECORDS_FILE_PULL, [])
    from datetime import datetime as dt
    now_iso = datetime.now().isoformat()
    demo = {
        'name': 'octocat/Hello-World',
        'url': 'https://github.com/octocat/Hello-World',
        'pullTime': now_iso,
        'stars': 100, 'forks': 50, 'path': '/app/data/repos/octocat/Hello-World',
        'config_snapshot': cfg_snapshot
    }
    records.insert(0, demo)
    _write_json(RECORDS_FILE_PULL, records)
    # DB 记录
    if session_scope and DBPullRecord:
        try:
            with session_scope() as s:
                s.add(DBPullRecord(
                    task_id=cfg.get('task_id'),
                    repo_full_name=demo['name'],
                    url=demo['url'],
                    pull_time=dt.fromisoformat(now_iso),
                    stars=demo['stars'],
                    forks=demo['forks'],
                    save_path=demo['path'],
                    result_status='queued',
                    rule=cfg.get('rule')
                ))
        except Exception:
            pass
    return jsonify({'success': True, 'data': {'status': 'queued', 'inserted': 1}})


@app.route('/api/pull/records', methods=['GET'])
def pull_records():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 30))
    keyword = request.args.get('keyword', '').strip()
    offset = (page - 1) * page_size

    # 优先从 DB 获取
    if session_scope and DBPullRecord:
        try:
            from sqlalchemy import select, desc, func, or_
            with session_scope() as s:
                # Build base query
                query = select(DBPullRecord)
                count_query = select(func.count(DBPullRecord.id))
                
                if keyword:
                    filter_condition = or_(
                        DBPullRecord.repo_full_name.ilike(f'%{keyword}%'),
                        DBPullRecord.summary.ilike(f'%{keyword}%')
                    )
                    query = query.filter(filter_condition)
                    count_query = count_query.filter(filter_condition)

                # Get total count
                total = s.execute(count_query).scalar()
                
                # Get paginated records
                rows = s.execute(
                    query
                    .order_by(desc(DBPullRecord.pull_time))
                    .offset(offset)
                    .limit(page_size)
                ).scalars().all()
                
                # Get tasks for these records to check status
                record_ids = [str(r.id) for r in rows]
                repo_names = [r.repo_full_name for r in rows]
                
                task_map = {}
                if record_ids or repo_names:
                    tasks_query = select(DBMakeTask).filter(
                        or_(
                            DBMakeTask.input_ref.in_(record_ids),
                            DBMakeTask.input_ref.in_(repo_names)
                        )
                    ).order_by(DBMakeTask.created_at.asc()) # Oldest first, so newest overwrites in map
                    
                    tasks = s.execute(tasks_query).scalars().all()
                    for t in tasks:
                        task_map[t.input_ref] = t

                records = []
                for r in rows:
                    # Check if task exists (prefer ID match, then name match)
                    task = task_map.get(str(r.id)) or task_map.get(r.repo_full_name)
                    
                    records.append({
                        'id': r.id,
                        'name': r.repo_full_name,
                        'url': r.url,
                        'pullTime': r.pull_time.isoformat() if r.pull_time else None,
                        'stars': r.stars,
                        'forks': r.forks,
                        'path': r.save_path,
                        'rule': r.rule,
                        'status': r.result_status,
                        'summary': r.summary,
                        'detail': r.detail,
                        'token_count': getattr(r, 'token_count', 0),
                        'task_id': task.task_id if task else None,
                        'task_status': task.status if task else None
                    })
                return jsonify({
                    'success': True, 
                    'data': records,
                    'total': total,
                    'page': page,
                    'pageSize': page_size
                })
        except Exception as e:
            print(f"DB Read Error: {e}")
            pass

    # 1. 读取 JSON 记录 (Fallback)
    records = _read_json(RECORDS_FILE_PULL, [])
    
    if keyword:
        kw = keyword.lower()
        records = [r for r in records if kw in (r.get('name') or '').lower() or kw in (r.get('summary') or '').lower()]
    
    total = len(records)
    start = offset
    end = start + page_size
    paginated_records = records[start:end]
    
    return jsonify({
        'success': True, 
        'data': paginated_records,
        'total': total,
        'page': page,
        'pageSize': page_size
    })


@app.route('/api/pull/repull', methods=['POST'])
def pull_repull():
    """Re-clone/update a single repository based on an existing pull record."""
    payload = request.get_json(silent=True) or {}
    record_id = payload.get('id')
    url = payload.get('url')
    path = payload.get('path')

    # Try to resolve from DB when id is provided
    if record_id and session_scope and DBPullRecord:
        try:
            with session_scope() as s:
                rec = s.get(DBPullRecord, int(record_id))
                if rec:
                    url = url or rec.url
                    path = path or rec.save_path
        except Exception as e:
            logger.error(f"Resolve pull record failed: {e}")

    if not url or not path:
        return jsonify({'success': False, 'message': 'Missing url or path'}), 400

    # Security check: ensure path is within DATA_DIR
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(DATA_DIR)):
        return jsonify({'success': False, 'message': 'Invalid path'}), 403

    def _repull_job(repo_url, repo_path, rec_id):
        try:
            logger.info(f"Re-pulling repo {repo_url} into {repo_path}")
            success = clone_repository(repo_url, repo_path)
            status = 'cloned' if success else 'failed'

            token_count = 0
            summary = None
            detail = None
            if success:
                try:
                    token_count = count_tokens_in_dir(repo_path)
                except Exception as e:
                    logger.error(f"Token count failed: {e}")
                try:
                    summary, detail = _generate_ai_summary_detail(repo_path)
                except Exception as e:
                    logger.error(f"Summary gen failed: {e}")

            # Update DB record if available
            if rec_id and session_scope and DBPullRecord:
                try:
                    with session_scope() as s:
                        rec = s.get(DBPullRecord, int(rec_id))
                        if rec:
                            rec.result_status = status
                            rec.token_count = token_count
                            if summary:
                                rec.summary = summary
                            if detail:
                                rec.detail = detail
                            rec.pull_time = datetime.now()
                            s.commit()
                except Exception as e:
                    logger.error(f"DB update failed in repull: {e}")

            # Update JSON fallback
            try:
                records = _read_json(RECORDS_FILE_PULL, [])
                updated = False
                for r in records:
                    if r.get('url') == repo_url:
                        r['status'] = status
                        r['token_count'] = token_count
                        if summary:
                            r['summary'] = summary
                        if detail:
                            r['detail'] = detail
                        r['pullTime'] = datetime.now().isoformat()
                        updated = True
                        break
                if updated:
                    _write_json(RECORDS_FILE_PULL, records)
            except Exception as e:
                logger.error(f"JSON update failed in repull: {e}")
        except Exception as e:
            logger.error(f"Re-pull job failed: {e}")

    t = threading.Thread(target=_repull_job, args=(url, abs_path, record_id))
    t.start()
    return jsonify({'success': True, 'data': {'status': 'started'}})


@app.route('/api/repo/readme', methods=['GET'])
def get_repo_readme():
    """Get README content for a given repo path."""
    path = request.args.get('path')
    if not path:
        return jsonify({'success': False, 'message': 'Missing path'}), 400
    
    # Security check: ensure path is within DATA_DIR
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(DATA_DIR)):
        return jsonify({'success': False, 'message': 'Invalid path'}), 403
        
    from pull.github_pull import get_readme_content
    content = get_readme_content(abs_path)
    return jsonify({'success': True, 'data': content})


# ========= 制作（Make/Article）API =========
@app.route('/api/config/model', methods=['GET', 'POST'])
def config_model():
    """Get or update model config."""
    config_file = os.path.join(CONFIG_DIR, 'model_config.json')
    
    # Get current config first
    current_config = {}
    if session_scope and DBMakeConfig:
        try:
            from sqlalchemy import select, desc
            with session_scope() as s:
                row = s.execute(select(DBMakeConfig).order_by(desc(DBMakeConfig.updated_at))).scalars().first()
                if row:
                    # Helper to decode bytes if necessary
                    def decode_if_bytes(v):
                        return v.decode('utf-8') if isinstance(v, bytes) else v

                    current_config = {
                        'provider': decode_if_bytes(row.provider),
                        'base_url': decode_if_bytes(row.base_url),
                        'model': decode_if_bytes(row.model),
                        'external_api_key': decode_if_bytes(row.external_api_key),
                        'engine_version': decode_if_bytes(row.engine_version) or 'v1',
                        'word_limit': row.word_limit or 8000,
                        'updated_at': row.updated_at.isoformat() if row.updated_at else None
                    }
        except Exception:
            pass
            
    if not current_config:
        current_config = _read_json(config_file, {})

    if request.method == 'POST':
        new_data = request.get_json(silent=True) or {}
        
        # Merge
        merged_config = current_config.copy()
        # Remove metadata keys if present in current_config but not relevant for saving
        merged_config.pop('updated_at', None)
        
        merged_config.update({k: v for k, v in new_data.items() if v is not None})
        
        _write_json(config_file, merged_config)
        
        # DB Persistence
        if session_scope and DBMakeConfig:
            try:
                with session_scope() as s:
                    s.add(DBMakeConfig(
                        provider=merged_config.get('provider'),
                        base_url=merged_config.get('base_url'),
                        model=merged_config.get('model'),
                        external_api_key=merged_config.get('external_api_key'),
                        engine_version=merged_config.get('engine_version', 'v1'),
                        word_limit=merged_config.get('word_limit', 8000),
                        updated_at=datetime.now()
                    ))
            except Exception:
                pass
                
        return jsonify({'success': True})
    else:
        return jsonify({'success': True, 'data': current_config})


@app.route('/api/config/model/test', methods=['POST'])
def test_model_config():
    """Test model configuration by sending a simple prompt."""
    payload = request.get_json(silent=True) or {}
    provider = payload.get('provider')
    api_key = payload.get('apiKey')
    base_url = payload.get('baseUrl')
    model_name = payload.get('modelName')
    
    if not provider or not api_key:
        return jsonify({'success': False, 'message': '缺少必要配置（Provider 或 API Key）'}), 400

    try:
        from llm.langchain_utils import get_llm
        from langchain_core.messages import HumanMessage
        
        llm = get_llm(provider, api_key, base_url, model_name)
        # Simple test
        response = llm.invoke([HumanMessage(content="你好！")])
        
        content = response.content
        if not content:
             content = "（无内容）"
             
        return jsonify({'success': True, 'message': '测试成功', 'reply': content})

    except Exception as e:
        return jsonify({'success': False, 'message': f'测试失败: {str(e)}'}), 500


def _process_article_task(task_id, input_ref):
    """Background task to generate article."""
    import time
    
    # Update task status helper
    def update_task_status(status, log_msg=None, content=None, detailed_content=None, thinking_content=None, repo_name=None):
        if session_scope and DBMakeTask:
            try:
                with session_scope() as s:
                    # Find by task_id (string)
                    t = s.execute(select(DBMakeTask).filter_by(task_id=task_id)).scalars().first()
                    if t:
                        t.status = status
                        t.log_file = f'make_{task_id}.log'
                        if content:
                            t.content = content
                        if detailed_content:
                            t.detailed_content = detailed_content
                        if thinking_content:
                            t.thinking_content = thinking_content
                        if repo_name:
                            t.repo_name = repo_name
                        if status == 'processing' and not t.started_at:
                            t.started_at = datetime.now()
                        if status in ['finished', 'failed', 'generated']:
                            t.finished_at = datetime.now()
            except Exception as e:
                print(f"Task update failed: {e}")
        
        # Log to file
        with open(os.path.join(LOGS_DIR, f'make_{task_id}.log'), 'a', encoding='utf-8') as f:
            if log_msg:
                f.write(f"{datetime.now().isoformat()} {log_msg}\n")
            f.write(f"{datetime.now().isoformat()} Status changed to {status}\n")

    update_task_status('processing', "Started processing task")
    
    try:
        # Check for revision feedback
        feedback = None
        existing_content = None
        if session_scope and DBMakeTask:
            try:
                from sqlalchemy import select
                with session_scope() as s:
                    t = s.execute(select(DBMakeTask).filter_by(task_id=task_id)).scalars().first()
                    if t:
                        feedback = t.feedback
                        existing_content = t.content
            except Exception:
                pass

        # 1. Get Repo Info
        update_task_status('processing', f"Step 1/4: Fetching repository info for '{input_ref}'...")
        repo_detail = ""
        repo_name = input_ref
        
        if session_scope and DBPullRecord:
            try:
                with session_scope() as s:
                    # Try ID first
                    if input_ref.isdigit():
                        rec = s.get(DBPullRecord, int(input_ref))
                    else:
                        rec = s.execute(select(DBPullRecord).filter_by(repo_full_name=input_ref)).scalars().first()
                    
                    if rec:
                        repo_name = rec.repo_full_name
                        repo_detail = rec.detail or rec.summary or ""
                        update_task_status('processing', f"Found record in DB. Repo: {repo_name}, Detail length: {len(repo_detail)}", repo_name=repo_name)
                        # If no detail in DB, try to read README
                        if not repo_detail and rec.save_path:
                             update_task_status('processing', f"Detail empty in DB, reading README from {rec.save_path}...", repo_name=repo_name)
                             from pull.github_pull import get_readme_content
                             repo_detail = get_readme_content(rec.save_path)
                             update_task_status('processing', f"Read README, length: {len(repo_detail)}", repo_name=repo_name)
            except Exception as e:
                update_task_status('processing', f"Error fetching repo info: {e}")
        
        if not repo_detail:
            update_task_status('failed', "No repository detail found. Please ensure the project is pulled and has a README.")
            return

        # 2. Get Prompt & Construct
        if feedback and existing_content:
            update_task_status('processing', "Step 2/4: Preparing revision prompt...")
            final_prompt = f"""你是一个专业的文章编辑。请根据以下反馈意见，对现有的文章进行修改和润色。

现有文章：
{existing_content}

项目详情：
{repo_detail[:10000]}

反馈意见：
{feedback}

请输出修改后的完整文章（Markdown格式，中文）。"""
        else:
            update_task_status('processing', "Step 2/4: Loading prompt template...")
            default_prompt = "请为项目 {name} 写一篇公众号文章。"
            prompt_tmpl = get_prompt('article_generation', default_prompt)
            update_task_status('processing', f"Loaded prompt template (Length: {len(prompt_tmpl)} chars)")
            final_prompt = f"{prompt_tmpl}\n\n项目名称：{repo_name}\n\n项目详情：\n{repo_detail[:15000]}"
        
        # 3. Call LLM
        update_task_status('processing', f"Step 3/4: Calling LLM to generate article for {repo_name}...")
        
        # Get Config
        provider = 'openai'
        base_url = ''
        model_name = ''
        api_key = ''
        engine_version = 'v1'
        word_limit = 8000
        
        if session_scope and DBMakeConfig:
            try:
                from sqlalchemy import select, desc
                with session_scope() as s:
                    row = s.execute(select(DBMakeConfig).order_by(desc(DBMakeConfig.updated_at))).scalars().first()
                    if row:
                        provider = row.provider
                        base_url = row.base_url
                        model_name = row.model
                        api_key = row.external_api_key
                        engine_version = row.engine_version or 'v1'
                        word_limit = row.word_limit or 8000
            except Exception:
                pass
        
        if not api_key:
             # Fallback to JSON
             cfg = _read_json(os.path.join(CONFIG_DIR, 'model_config.json'), {})
             provider = cfg.get('provider', 'openai')
             base_url = cfg.get('base_url', '')
             model_name = cfg.get('model', '')
             api_key = cfg.get('external_api_key', '')
             engine_version = cfg.get('engine_version', 'v1')
             word_limit = cfg.get('word_limit', 8000)

        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')

        if not api_key:
            update_task_status('failed', "No API Key configured. Please configure the model in settings.")
            return

        update_task_status('processing', f"Using Model: {provider}/{model_name}")

        # Use new article generator
        try:
            from article_gen.generator import generate_article_content
        except ImportError:
            from article_gen.generator import generate_article_content

        llm_config = {
            'provider': provider,
            'api_key': api_key,
            'base_url': base_url,
            'model_name': model_name,
            'engine_version': engine_version,
            'word_limit': word_limit
        }

        # Determine repo path
        repo_path = None
        if session_scope and DBPullRecord:
            try:
                with session_scope() as s:
                    if input_ref.isdigit():
                        rec = s.get(DBPullRecord, int(input_ref))
                    else:
                        rec = s.execute(select(DBPullRecord).filter_by(repo_full_name=input_ref)).scalars().first()
                    if rec:
                        repo_path = rec.save_path
            except:
                pass
        
        if not repo_path or not os.path.exists(repo_path):
             # Try to guess path if not found in DB or DB unavailable
             repo_path = os.path.join(DATA_DIR, 'repos', repo_name)
             if not os.path.exists(repo_path):
                 # Try splitting repo_name
                 parts = repo_name.split('/')
                 if len(parts) == 2:
                     repo_path = os.path.join(DATA_DIR, 'repos', parts[0], parts[1])

        if not repo_path or not os.path.exists(repo_path):
            update_task_status('failed', f"Repository path not found for {repo_name}")
            return

        def log_wrapper(msg):
            update_task_status('processing', msg)

        article_result = generate_article_content(
            repo_path=repo_path,
            repo_name=repo_name,
            user_prompt=final_prompt,
            llm_config=llm_config,
            log_callback=log_wrapper
        )
        
        article_content = ""
        detailed_content = None
        thinking_content = None
        
        if isinstance(article_result, dict):
            article_content = article_result.get("final_content")
            detailed_content = article_result.get("detailed_content")
            thinking_content = article_result.get("thinking_content")
        else:
            article_content = article_result
        
        if not article_content:
            update_task_status('failed', "LLM returned empty content. Please check model configuration and quota.")
            return
            
        update_task_status('processing', f"LLM generation successful. Content length: {len(article_content)}")

        # 4. Save Article
        update_task_status('processing', "Step 4/4: Saving article file...")
        articles_dir = ARTICLES_DIR
        os.makedirs(articles_dir, exist_ok=True)
        filename = f"{repo_name.replace('/', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(articles_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article_content)
            
        update_task_status('generated', f"Article saved to {filename}", content=article_content, detailed_content=detailed_content, thinking_content=thinking_content)
        
    except Exception as e:
        update_task_status('failed', f"Unexpected error: {e}")


@app.route('/api/article/create_task', methods=['POST'])
def create_article_task():
    """Create a new article production task from a pull record."""
    data = request.get_json(silent=True) or {}
    pull_record_id = data.get('pull_record_id')
    repo_name = data.get('repo_name')
    
    if not pull_record_id and not repo_name:
        return jsonify({'success': False, 'message': 'Missing pull_record_id or repo_name'}), 400
        
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{pull_record_id or 'manual'}"
    
    # DB Record
    if session_scope and DBMakeTask:
        try:
            with session_scope() as s:
                # Try to resolve repo_name if missing
                if not repo_name and pull_record_id and DBPullRecord:
                    try:
                        rec = s.get(DBPullRecord, int(pull_record_id))
                        if rec:
                            repo_name = rec.repo_full_name
                    except Exception:
                        pass

                s.add(DBMakeTask(
                    task_id=task_id,
                    input_ref=str(pull_record_id) if pull_record_id else repo_name,
                    repo_name=repo_name,
                    status='queued',
                    created_at=datetime.now()
                ))
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
            
    # JSON Fallback
    tasks = _read_json(TASKS_FILE_MAKE, [])
    task = {
        'id': task_id,
        'input_ref': str(pull_record_id) if pull_record_id else repo_name,
        'repo_name': repo_name,
        'status': 'queued',
        'createdAt': datetime.now().isoformat(),
        'log': '[queued] Task created manually\n'
    }
    tasks.insert(0, task)
    _write_json(TASKS_FILE_MAKE, tasks)
    
    # Start processing in background
    t = threading.Thread(target=_process_article_task, args=(task_id, str(pull_record_id) if pull_record_id else repo_name))
    t.start()
    
    return jsonify({'success': True, 'data': task})


@app.route('/api/make/tasks', methods=['GET'])
def make_tasks():
    # 优先 DB
    if session_scope and DBMakeTask:
        try:
            from sqlalchemy import select, desc
            with session_scope() as s:
                rows = s.execute(select(DBMakeTask).order_by(desc(DBMakeTask.created_at))).scalars().all()
                data = []
                for r in rows:
                    # Try to find repo name if input_ref is ID
                    repo_name = r.repo_name or r.input_ref
                    if r.input_ref and r.input_ref.isdigit() and DBPullRecord and not r.repo_name:
                        try:
                            rec = s.execute(select(DBPullRecord).filter_by(id=int(r.input_ref))).scalars().first()
                            if rec:
                                repo_name = rec.repo_full_name
                        except:
                            pass
                            
                    data.append({
                        'id': r.task_id or str(r.id),
                        'input_ref': r.input_ref,
                        'repo_name': repo_name,
                        'status': r.status,
                        'createdAt': r.created_at.isoformat() if r.created_at else None
                    })
                return jsonify({'success': True, 'data': data})
        except Exception:
            pass
    return jsonify({'success': True, 'data': _read_json(TASKS_FILE_MAKE, [])})


@app.route('/api/make/enqueue', methods=['POST'])
def make_enqueue():
    tasks = _read_json(TASKS_FILE_MAKE, [])
    payload = request.get_json(silent=True) or {}
    task_id = payload.get('task_id') or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    input_ref = payload.get('input_ref')
    task = {
        'id': task_id,
        'input_ref': input_ref,
        'status': 'queued',
        'createdAt': datetime.now().isoformat(),
        'log': '[queued] 已入队（占位）\n'
    }
    tasks.insert(0, task)
    _write_json(TASKS_FILE_MAKE, tasks)
    # DB 记录
    if session_scope and DBMakeTask:
        try:
            with session_scope() as s:
                s.add(DBMakeTask(task_id=task_id, input_ref=input_ref, status='queued', created_at=datetime.now()))
        except Exception:
            pass
    return jsonify({'success': True, 'data': task})


@app.route('/api/make/logs/<task_id>', methods=['GET'])
def make_logs(task_id):
    path = os.path.join(LOGS_DIR, f'make_{task_id}.log')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = '[placeholder] 暂无日志\n'
    return jsonify({'success': True, 'data': {'task_id': task_id, 'log': content}})


@app.route('/api/files/<path:filename>')
def download_file(filename):
    """Serve generated files."""
    directory = os.path.join(os.path.dirname(__file__), 'data', 'generated_docs')
    # Force download for markdown files
    as_attachment = filename.lower().endswith('.md')
    return send_from_directory(directory, filename, as_attachment=as_attachment)


@app.route('/api/publish/pending', methods=['GET'])
def get_pending_publish_articles():
    """Get approved articles ready for publishing."""
    if not session_scope or not DBMakeTask:
        return jsonify({'success': False, 'message': 'Database not available'})
        
    try:
        from sqlalchemy import select, desc
        with session_scope() as s:
            rows = s.execute(select(DBMakeTask).filter_by(status='approved').order_by(desc(DBMakeTask.finished_at))).scalars().all()
            data = []
            for r in rows:
                # Try to fix missing repo_name
                if not r.repo_name and r.input_ref:
                    if not r.input_ref.isdigit():
                        r.repo_name = r.input_ref
                    elif DBPullRecord:
                        try:
                            prec = s.get(DBPullRecord, int(r.input_ref))
                            if prec:
                                r.repo_name = prec.repo_full_name
                        except Exception:
                            pass

                # Construct filenames based on convention
                title = r.repo_name or f"Article_{r.task_id}"
                safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
                base_filename = f"{r.task_id}_{safe_title}"
                
                data.append({
                    'id': r.id,
                    'task_id': r.task_id,
                    'title': title,
                    'repo_name': r.repo_name,
                    'article_type': r.article_type,
                    'status': r.status,
                    'content': r.content,
                    'approved_at': r.finished_at.isoformat() if r.finished_at else None,
                    'files': {
                        'html': f"/api/files/{base_filename}.html",
                        'pdf': f"/api/files/{base_filename}.pdf",
                        'docx': f"/api/files/{base_filename}.docx",
                        'md': f"/api/files/{base_filename}.md"
                    }
                })
            return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========= 发布（Publish）API =========
@app.route('/api/publish/config', methods=['GET', 'POST'])
def publish_config():
    cfg_path = os.path.join(CONFIG_DIR, 'publish_config.json')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        allow = {'platforms', 'account', 'apiKey', 'publishTime'}
        saved = {k: data.get(k) for k in allow}
        saved['updated_at'] = datetime.now().isoformat()
        _write_json(cfg_path, saved)
        # DB 持久化
        if session_scope and 'DBPublishConfig' in globals() and DBPublishConfig:
            try:
                from datetime import time
                pt = None
                if isinstance(saved.get('publishTime'), str) and len(saved['publishTime']) >= 4:
                    hh, mm = saved['publishTime'].split(':')[0:2]
                    pt = time(int(hh), int(mm))
                with session_scope() as s:
                    s.add(DBPublishConfig(
                        platforms=saved.get('platforms'),
                        account=saved.get('account'),
                        api_key=saved.get('apiKey'),
                        publish_time=pt,
                        updated_at=datetime.now()
                    ))
            except Exception:
                pass
        return jsonify({'success': True, 'data': saved})
    else:
        # 优先 DB
        if session_scope and 'DBPublishConfig' in globals() and DBPublishConfig:
            try:
                from sqlalchemy import select, desc
                with session_scope() as s:
                    row = s.execute(select(DBPublishConfig).order_by(desc(DBPublishConfig.updated_at))).scalars().first()
                    if row:
                        # Helper to decode bytes if necessary
                        def decode_if_bytes(v):
                            return v.decode('utf-8') if isinstance(v, bytes) else v

                        return jsonify({'success': True, 'data': {
                            'platforms': row.platforms,
                            'account': decode_if_bytes(row.account),
                            'apiKey': decode_if_bytes(row.api_key),
                            'publishTime': row.publish_time.strftime('%H:%M') if row.publish_time else None,
                            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                        }})
            except Exception:
                pass
        return jsonify({'success': True, 'data': _read_json(cfg_path, {})})


@app.route('/api/publish/test', methods=['POST'])
def publish_test():
    payload = request.get_json(silent=True) or {}
    history = _read_json(RECORDS_FILE_PUBLISH, [])
    demo = {
        'title': payload.get('title') or 'GitHub 每周精选',
        'platform': (payload.get('platform') or '微信公众号'),
        'time': datetime.now().isoformat(),
        'status': 'queued',
        'url': payload.get('url') or '#'
    }
    history.insert(0, demo)
    _write_json(RECORDS_FILE_PUBLISH, history)
    # DB 记录
    if session_scope and DBPublishHistory:
        try:
            with session_scope() as s:
                from datetime import datetime as dt
                s.add(DBPublishHistory(title=demo['title'], platform=demo['platform'], time=dt.fromisoformat(demo['time']), status=demo['status'], url=demo['url']))
        except Exception:
            pass
    return jsonify({'success': True, 'data': demo})


@app.route('/api/publish/history', methods=['GET'])
def publish_history():
    # 优先 DB
    if session_scope and DBPublishHistory:
        try:
            from sqlalchemy import select, desc
            with session_scope() as s:
                rows = s.execute(select(DBPublishHistory).order_by(desc(DBPublishHistory.time))).scalars().all()
                data = []
                for r in rows:
                    data.append({
                        'title': r.title,
                        'platform': r.platform,
                        'time': r.time.isoformat() if r.time else None,
                        'status': r.status,
                        'url': r.url,
                    })
                return jsonify({'success': True, 'data': data})
        except Exception:
            pass
    return jsonify({'success': True, 'data': _read_json(RECORDS_FILE_PUBLISH, [])})


@app.route('/api/publish/links', methods=['GET'])
def publish_links():
    return jsonify({'success': True, 'data': _read_json(LINKS_FILE_PUBLISH, [])})


@app.route('/api/pull/deduplicate', methods=['POST'])
def deduplicate_records():
    """Deduplicate pull records, keeping the latest one."""
    if not session_scope or not DBPullRecord:
        return jsonify({'success': False, 'message': 'Database not available'})
    
    try:
        with session_scope() as s:
            from sqlalchemy import func, select
            
            # Get duplicate URLs
            dupes = s.execute(
                select(DBPullRecord.url, func.count(DBPullRecord.id))
                .group_by(DBPullRecord.url)
                .having(func.count(DBPullRecord.id) > 1)
            ).all()
            
            deleted_count = 0
            for url, count in dupes:
                # Get all records for this URL, ordered by pull_time desc (latest first)
                records = s.execute(
                    select(DBPullRecord)
                    .filter_by(url=url)
                    .order_by(DBPullRecord.pull_time.desc(), DBPullRecord.id.desc())
                ).scalars().all()
                
                # Keep the first one (latest), delete others
                if len(records) > 1:
                    to_delete = records[1:]
                    for r in to_delete:
                        s.delete(r)
                        deleted_count += 1
            
            s.commit()
            return jsonify({'success': True, 'message': f'Deduplicated {deleted_count} records'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/pull/reanalyze_all', methods=['POST'])
def reanalyze_all():
    """Re-analyze all existing records using AI."""
    if not session_scope:
        return jsonify({'code': 500, 'message': 'Database not initialized'})
    
    count = 0
    updated_names = []
    try:
        with session_scope() as session:
            # 1. Sync from JSON to DB
            json_records = _read_json(RECORDS_FILE_PULL, [])
            db_paths = {r.save_path for r in session.query(DBPullRecord.save_path).all() if r.save_path}
            
            for jr in json_records:
                path = jr.get('path')
                if path and path not in db_paths:
                    # Insert into DB
                    new_rec = DBPullRecord(
                        repo_full_name=jr.get('name'),
                        url=jr.get('url'),
                        pull_time=datetime.fromisoformat(jr.get('pullTime')) if jr.get('pullTime') else datetime.now(),
                        stars=jr.get('stars', 0),
                        forks=jr.get('forks', 0),
                        save_path=path,
                        result_status=jr.get('status', 'cloned'),
                        rule=jr.get('rule', 'manual'),
                        summary=jr.get('summary')[:60000] if jr.get('summary') else None,
                        detail=jr.get('detail')[:60000] if jr.get('detail') else None
                    )
                    session.add(new_rec)
                    db_paths.add(path)
            session.commit()

            # 2. Re-analyze all DB records
            records = session.query(DBPullRecord).all()
            for record in records:
                # Determine path
                repo_path = record.save_path
                if not repo_path:
                    continue
                    
                if not os.path.exists(repo_path):
                    # Try relative to data dir
                    data_dir = os.path.join(os.path.dirname(__file__), 'data')
                    possible_path = os.path.join(data_dir, os.path.basename(repo_path))
                    if os.path.exists(possible_path):
                        repo_path = possible_path
                    else:
                        continue
                
                # Calculate Tokens
                try:
                    token_count = count_tokens_in_dir(repo_path)
                    record.token_count = token_count
                except Exception:
                    pass

                # Generate
                summary, detail = _generate_ai_summary_detail(repo_path)
                record.summary = summary[:60000] if summary else summary
                record.detail = detail[:60000] if detail else detail
                updated_names.append(record.repo_full_name or record.url)
                count += 1
                
        return jsonify({
            'code': 200, 
            'message': f'Successfully re-analyzed {count} projects',
            'data': updated_names
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)})


if __name__ == '__main__':
    # 从环境变量获取配置，默认值用于开发环境
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.run(host=host, port=port, debug=debug)
