# -*- coding: utf-8 -*-
"""
MCP 集成与 LangChain 管道占位实现
- 通过 MCP 客户端抓取 GitHub 页面或 API
- 使用外部 AI 模型对项目进行分析
- 结合 SKILL 技术（技能/工具调度）给出操作指导

此文件为最小可用占位，避免破坏现有服务；实际模型与 MCP 端点需后续配置。
"""
from typing import Dict, Any, List, Optional
import os
import requests
import tiktoken

# 支持中国国内模型（OpenAI 兼容模式）：deepseek、qwen(dashscope)
PROVIDER_DEFAULTS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": os.getenv("MODEL_NAME", "deepseek-chat"),
    },
    "qwen": {
        # 阿里云 DashScope 兼容模式
        "base_url": os.getenv("MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        "model": os.getenv("MODEL_NAME", "qwen-plus"),
    },
    "copilot": {
        # 占位：Copilot Agent（需要企业/预览接口），假设 OpenAI 兼容
        "base_url": os.getenv("COPILOT_BASE_URL", "https://api.githubcopilot.com/v1"),
        "model": os.getenv("COPILOT_MODEL", "copilot-agent"),
    },
    "cursor": {
        # 占位：Cursor Agent（需要对应服务端接口），假设 OpenAI 兼容
        "base_url": os.getenv("CURSOR_BASE_URL", "https://api.cursor.sh/v1"),
        "model": os.getenv("CURSOR_MODEL", "cursor-agent"),
    },
}

def chat_completion_openai_compatible(api_key: str, prompt: str, provider: str = "deepseek", base_url: Optional[str] = None, model: Optional[str] = None) -> str:
    try:
        try:
            from backend.llm.langchain_utils import get_llm
        except ImportError:
            from llm.langchain_utils import get_llm
        from langchain_core.messages import HumanMessage
        
        llm = get_llm(provider, api_key, base_url, model)
        
        system_prompt = "You are an expert software analyst. You must answer in Chinese. If the input content is in English or another language, translate the key information into Chinese. Ensure all large blocks of text are in Chinese. Your response must be logically rigorous, semantically smooth, and factually accurate."
        
        # We can use invoke_chain or just invoke directly
        from langchain_core.messages import SystemMessage
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt)
        ])
        return response.content
    except Exception as e:
        return f"LLM Error: {str(e)}"

# 轻量占位：模拟 MCP 客户端调用（实际需替换为 mcp 客户端实现）
class MockMCPClient:
    def fetch_github_repo(self, repo_full_name: str) -> Dict[str, Any]:
        # 优先使用 GitHub API，避免直接抓取 HTML；需要令牌时读取环境变量
        token = os.getenv('GITHUB_TOKEN')
        headers = {'Accept': 'application/vnd.github+json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        r = requests.get(f'https://api.github.com/repos/{repo_full_name}', headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()

# 轻量占位：模拟 LangChain 外部模型调用
def analyze_repo_with_llm(repo: Dict[str, Any], api_key: str | None = None, provider: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    # 构造分析提示词
    name = repo.get('full_name')
    stars = repo.get('stargazers_count', 0)
    language = repo.get('language')
    desc = repo.get('description') or ""
    
    # 如果提供了详细内容（如 README），则加入分析
    content_summary = ""
    if content:
        # Use tiktoken to count tokens
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            token_count = len(enc.encode(content))
        except Exception:
            token_count = len(content) // 4

        if token_count > 18000: # Limit to 18k to be safe under 20k
             try:
                 try:
                     from backend.llm.langchain_utils import get_llm, summarize_large_content
                 except ImportError:
                     from llm.langchain_utils import get_llm, summarize_large_content
                 # 需要先获取 LLM 实例
                 # 这里逻辑稍微有点绕，因为 get_llm 需要 api_key，而 api_key 可能在下面才获取
                 # 为了简化，我们先尝试获取配置
                 if not api_key:
                     # 尝试从 DB 获取 (重复代码，但为了安全)
                     try:
                        try:
                            from utils.db import session_scope, MakeConfig
                        except ImportError:
                            from backend.utils.db import session_scope, MakeConfig
                        if session_scope:
                            with session_scope() as s:
                                cfg = s.query(MakeConfig).first()
                                if cfg and cfg.external_api_key:
                                    api_key = cfg.external_api_key
                                    provider = cfg.provider or provider
                                    base_url = cfg.base_url or base_url
                                    model = cfg.model or model
                     except: pass
                 
                 if api_key:
                     llm = get_llm(provider or "deepseek", api_key, base_url, model)
                     content_summary = summarize_large_content(llm, content, chunk_size=15000)
                     content_summary = f"\n\n项目详细内容摘要：\n{content_summary}"
                 else:
                     content_summary = f"\n\n项目详细内容（截断）：\n{content[:5000]}..."
             except Exception as e:
                 content_summary = f"\n\n内容摘要失败: {str(e)}\n内容截断: {content[:2000]}"
        else:
            content_summary = f"\n\n项目详细内容：\n{content}"

    prompt = (
        f"请分析 GitHub 项目 {name}，语言 {language}，stars={stars}。"
        f"简述项目价值、适用场景、潜在风险，并给出 3 条行动建议（中文精炼）。\n描述：{desc}"
        f"{content_summary}\n\n"
        f"要求：回答必须逻辑严谨，语义通顺，符合事实。"
    )

    guidance = [
        {"skill": "code-review", "action": "检查 README 与 CI 状态", "priority": "high"},
        {"skill": "roadmap", "action": "查看带 good first issue 的问题", "priority": "medium"},
    ]

    # 使用外部模型（OpenAI 兼容）
    summary = None
    
    # 如果未提供 api_key，尝试从数据库加载配置
    if not api_key:
        try:
            try:
                from utils.db import session_scope, MakeConfig
            except ImportError:
                from backend.utils.db import session_scope, MakeConfig
                
            if session_scope:
                with session_scope() as s:
                    config = s.query(MakeConfig).first()
                    if config and config.external_api_key:
                        api_key = config.external_api_key
                        provider = config.provider or provider
                        base_url = config.base_url or base_url
                        model = config.model or model
        except Exception as e:
            print(f"Failed to load config from DB: {e}")

    meta = {"api_key_forwarded": bool(api_key)}
    if api_key:
        # 优先从环境变量读取默认 provider/base_url/model
        provider = provider or os.getenv("MODEL_PROVIDER", "deepseek")
        base_url = base_url or os.getenv("MODEL_BASE_URL")
        model = model or os.getenv("MODEL_NAME")
        try:
            summary = chat_completion_openai_compatible(api_key, prompt, provider=provider, base_url=base_url, model=model)
            meta.update({"provider": provider, "base_url": base_url, "model": model})
        except Exception as e:
            summary = f"外部模型调用失败: {e}"
            meta.update({"error": str(e)})

    if not summary:
        summary = f"{name} uses {language}, stars={stars}."

    return {"summary": summary, "guidance": guidance, "meta": meta}

# 轻量占位：公众号 MCP 接入（若可用）
def try_wechat_mcp_publish(title: str, content: str) -> Dict[str, Any]:
    # 实际实现需连接公众号 MCP；此处仅返回占位结果
    if not os.getenv('WECHAT_APP_ID'):
        return {"enabled": False, "message": "WeChat MCP not configured"}
    return {"enabled": True, "message": "WeChat MCP publish queued (mock)"}


def analyze_github_repo(repo_full_name: str, api_key: str | None = None, provider: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None, content: Optional[str] = None) -> Dict[str, Any]:
    mcp = MockMCPClient()
    repo = mcp.fetch_github_repo(repo_full_name)
    analysis = analyze_repo_with_llm(repo, api_key=api_key, provider=provider, base_url=base_url, model=model, content=content)
    wechat = try_wechat_mcp_publish(title=f"分析：{repo_full_name}", content=analysis.get("summary", ""))
    return {"repo": repo, "analysis": analysis, "wechat": wechat}
