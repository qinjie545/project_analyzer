import logging
import os
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from requests.exceptions import RequestException

try:
    from backend.utils.store import DATA_DIR
    from backend.utils.token_counter import count_tokens_in_dir
except ImportError:
    from utils.store import DATA_DIR
    from utils.token_counter import count_tokens_in_dir

REPOS_DIR = os.path.join(DATA_DIR, 'repos')
os.makedirs(REPOS_DIR, exist_ok=True)

GITHUB_API = 'https://api.github.com'
DEFAULT_GITHUB_TIMEOUT = int(os.getenv('GITHUB_API_TIMEOUT', '30'))
MAX_GITHUB_RETRIES = int(os.getenv('GITHUB_API_MAX_RETRIES', '3'))
GIT_COMMAND_RETRIES = int(os.getenv('GIT_COMMAND_RETRIES', '2'))
DEFAULT_GIT_HTTP_VERSION = os.getenv('GIT_HTTP_VERSION', 'HTTP/1.1')

logger = logging.getLogger(__name__)


def get_readme_content(repo_dir: str) -> str:
    """Try to find and read README file from repo directory."""
    if not os.path.exists(repo_dir):
        return ""
    
    # Find README file (case insensitive)
    readme_file = None
    for f in os.listdir(repo_dir):
        if f.lower().startswith('readme'):
            readme_file = f
            break
    
    if not readme_file:
        return ""
        
    try:
        with open(os.path.join(repo_dir, readme_file), 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""


def generate_summary(repo_dir: str) -> str:
    """Generate a simple summary from README."""
    content = get_readme_content(repo_dir)
    if not content:
        return "暂无介绍"
    
    # Simple extraction: take first 300 chars, remove markdown headings
    lines = content.split('\n')
    clean_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip badges (lines starting with [! or [![ )
        if line.startswith('[!') or line.startswith('[!['):
            continue
        # Remove heading markers
        clean_line = line.lstrip('#').strip()
        if clean_line:
            clean_lines.append(clean_line)
            
    summary = ' '.join(clean_lines)[:300]
    if len(summary) >= 300:
        summary += '...'
    return summary


def _run_git_command(cmd: List[str], retries: int = GIT_COMMAND_RETRIES) -> bool:
    env = os.environ.copy()
    env.setdefault('GIT_HTTP_VERSION', DEFAULT_GIT_HTTP_VERSION)
    for attempt in range(1, retries + 1):
        try:
            subprocess.check_call(cmd, env=env)
            return True
        except subprocess.CalledProcessError as exc:
            logger.error(f"Git command failed (attempt {attempt}/{retries}): {cmd} -> {exc}")
            if attempt == retries:
                return False
            sleep_time = 2 ** (attempt - 1)
            logger.debug(f"Retrying git command in {sleep_time}s")
            time.sleep(sleep_time)
    return False


def clone_repository(url: str, dest_dir: str) -> bool:
    logger.debug(f"Cloning {url} to {dest_dir}")
    if os.path.exists(dest_dir) and os.path.isdir(dest_dir):
        # already exists, try to pull
        logger.debug(f"Directory exists, pulling: {dest_dir}")
        return _run_git_command(['git', '-C', dest_dir, 'pull'])

    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
    logger.debug(f"Cloning new repo: {url}")
    if _run_git_command(['git', 'clone', '--depth', '1', url, dest_dir]):
        return True

    logger.error(f"Git clone failed after retries: {url}")
    return False


def _git_clone(url: str, dest_dir: str) -> bool:
    return clone_repository(url, dest_dir)


def _request_with_retry(endpoint: str, params: Dict, headers: Dict) -> requests.Response:
    last_exc: Optional[RequestException] = None
    for attempt in range(1, MAX_GITHUB_RETRIES + 1):
        try:
            resp = requests.get(
                endpoint,
                params=params,
                headers=headers,
                timeout=DEFAULT_GITHUB_TIMEOUT,
            )
            resp.raise_for_status()
            return resp
        except RequestException as exc:
            last_exc = exc
            logger.warning(
                "GitHub request failed (attempt %s/%s): %s", attempt, MAX_GITHUB_RETRIES, exc
            )
            if attempt == MAX_GITHUB_RETRIES:
                break
            sleep_time = min(2 ** (attempt - 1), 16)
            logger.debug("Retrying GitHub request in %ss", sleep_time)
            time.sleep(sleep_time)
    if last_exc:
        raise last_exc
    raise RuntimeError("GitHub request failed without an exception")


def search_github_repos(keyword: str, token: Optional[str] = None, sort: str = 'stars', order: str = 'desc', per_page: int = 10) -> List[Dict]:
    params = {
        'q': keyword,
        'order': order,
        'per_page': per_page
    }
    if sort:
        params['sort'] = sort
    
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    logger.debug(f"Requesting GitHub API: {GITHUB_API}/search/repositories with params={params}")
    resp = _request_with_retry(f'{GITHUB_API}/search/repositories', params=params, headers=headers)
    data = resp.json()
    items = data.get('items', [])
    logger.debug(f"GitHub API returned {len(items)} items")
    return items


def run_github_pull(keyword: str, limit: int = 10, sort: str = 'stars', token: Optional[str] = None, simulate: bool = False):
    """
    Pull repositories from GitHub matching keyword and store under data/repos/{owner}/{repo}
    Returns list of result dicts for records writing.
    """
    results: List[Dict] = []
    now = datetime.now()
    if simulate:
        # Create a placeholder directory
        owner, repo = 'octocat', 'Hello-World'
        url = f'https://github.com/{owner}/{repo}.git'
        dest = os.path.join(REPOS_DIR, owner, repo)
        os.makedirs(dest, exist_ok=True)
        results.append({
            'name': f'{owner}/{repo}',
            'url': f'https://github.com/{owner}/{repo}',
            'pullTime': now,
            'stars': 100,
            'forks': 50,
            'path': dest,
            'status': 'simulated'
        })
        return results

    items = search_github_repos(keyword, token=token, sort=sort, order='desc', per_page=limit)
    for it in items:
        full_name = it.get('full_name') or f"{it.get('owner',{}).get('login','unknown')}/{it.get('name','unknown')}"
        owner = full_name.split('/')[0]
        repo = full_name.split('/')[1]
        html_url = it.get('html_url')
        stars = it.get('stargazers_count') or 0
        forks = it.get('forks_count') or 0
        dest = os.path.join(REPOS_DIR, owner, repo)
        ok = _git_clone(f'{html_url}.git', dest)
        
        token_count = 0
        if ok:
            try:
                token_count = count_tokens_in_dir(dest)
            except Exception:
                pass

        results.append({
            'name': full_name,
            'url': html_url,
            'pullTime': now,
            'stars': stars,
            'forks': forks,
            'path': dest,
            'status': 'cloned' if ok else 'failed',
            'token_count': token_count
        })
    return results
