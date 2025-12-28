from typing import Dict
try:
    from backend.article_gen import generator_v1
    from backend.article_gen import generator_v2
except ImportError:
    from article_gen import generator_v1
    from article_gen import generator_v2

def generate_article_content(repo_path: str, repo_name: str, user_prompt: str, llm_config: Dict, log_callback=None) -> str:
    engine_version = llm_config.get('engine_version', 'v1')
    
    if log_callback:
        log_callback(f"Using Article Generation Engine: {engine_version.upper()}")

    if engine_version == 'v2':
        return generator_v2.generate_article_content(repo_path, repo_name, user_prompt, llm_config, log_callback)
    else:
        return generator_v1.generate_article_content(repo_path, repo_name, user_prompt, llm_config, log_callback)
