import os
import json
import re
from typing import List, Set, Dict
try:
    from backend.llm.langchain_utils import get_llm
    from backend.utils.text_utils import sanitize_mermaid_content
except ImportError:
    from llm.langchain_utils import get_llm
    from utils.text_utils import sanitize_mermaid_content
from langchain_core.messages import SystemMessage, HumanMessage

# 20k tokens ~ 80k chars. We use a safe buffer.
MAX_CHARS_PER_CALL = 60000 

def get_file_tree(repo_path: str) -> str:
    """Generate a visual file tree of the repository."""
    tree_str = ""
    repo_path = os.path.abspath(repo_path)
    
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden dirs and common ignore dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'dist', 'build']]
        
        level = root.replace(repo_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree_str += '{}{}/\n'.format(indent, os.path.basename(root))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.startswith('.') and not f.endswith(('.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf')):
                tree_str += '{}{}\n'.format(subindent, f)
                
        # Limit tree size to avoid context overflow just for tree
        if len(tree_str) > 20000:
            tree_str += "\n...(tree truncated)...\n"
            break
             
    return tree_str

def read_file_content(repo_path: str, file_path: str) -> str:
    """Read content of a file, ensuring it's within the repo."""
    # Handle potential leading slash or relative path issues
    file_path = file_path.lstrip('/')
    full_path = os.path.join(repo_path, file_path)
    
    # Security check
    if not os.path.abspath(full_path).startswith(os.path.abspath(repo_path)):
        return ""

    if not os.path.exists(full_path):
        # Try to find by name if path is inexact (simple heuristic)
        for root, _, files in os.walk(repo_path):
            if os.path.basename(file_path) in files:
                full_path = os.path.join(root, os.path.basename(file_path))
                break
        else:
            return ""

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

def extract_json_list(text: str) -> List[str]:
    """Extract a JSON list of strings from text."""
    try:
        # Try direct parse
        return json.loads(text)
    except:
        pass
        
    # Try regex
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            pass
            
    return []

def generate_article_content(repo_path: str, repo_name: str, user_prompt: str, llm_config: Dict, log_callback=None) -> str:
    """
    Generate article content using multi-step AI interaction (V2 Engine).
    Directly generates the final article without intermediate detailed documentation.
    
    Args:
        repo_path: Path to the repository
        repo_name: Name of the repository
        user_prompt: The goal/prompt for the article
        llm_config: Configuration for LLM (provider, api_key, etc.)
        log_callback: Function to log progress (msg)
    
    Returns:
        Generated article content (Markdown)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        print(f"[ArticleGenV2] {msg}")

    provider = llm_config.get('provider', 'openai')
    api_key = llm_config.get('api_key')
    base_url = llm_config.get('base_url')
    model_name = llm_config.get('model_name')

    llm = get_llm(provider, api_key, base_url, model_name, max_tokens=32000)
    word_limit = llm_config.get('word_limit', 8000)
    
    # Step 1: Get File Tree
    log("Step 1: Generating file tree...")
    file_tree = get_file_tree(repo_path)
    log(f"File Tree Content (First 2000 chars):\n{file_tree[:2000]}..." if len(file_tree) > 2000 else f"File Tree Content:\n{file_tree}")
    
    # Step 2: Ask for files to read
    log("Step 2: Analyzing file tree to select files...")
    system_prompt = "You are an expert software architect. You analyze codebases to write articles. Your response must be logically rigorous, semantically smooth, and factually accurate. Maintain a professional perspective, do not exaggerate. Be realistic and rigorous. Avoid words like 'extremely high', 'huge', 'perfect', etc. unless strictly proven. Focus on technical facts."
    
    prompt_1 = f"""Project: {repo_name}
File Tree:
{file_tree}

Goal: {user_prompt}

Based on the file tree and the goal, which files should I read to understand the project? 
Select up to 10 most important files.
Return ONLY a JSON list of file paths (strings). Example: ["src/main.py", "README.md"]
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt_1)
    ]
    
    response = llm.invoke(messages)
    files_to_read = extract_json_list(response.content)
    if not isinstance(files_to_read, list):
        files_to_read = []
        
    log(f"LLM requested initial files: {files_to_read}")

    # Step 3: Loop
    context = ""
    read_files: Set[str] = set()
    
    # Initial read
    for f in files_to_read:
        if f not in read_files:
            content = read_file_content(repo_path, f)
            if content:
                # Check token limit
                if len(context) + len(content) > MAX_CHARS_PER_CALL: 
                    log(f"Context limit reached, skipping {f}")
                    break
                context += f"\n\n--- File: {f} ---\n{content}"
                read_files.add(f)

    # Iteration
    for i in range(3):
        log(f"Step 3.{i+1}: Refining context (Current size: {len(context)} chars)...")
        
        prompt_loop = f"""Current Context (Files read: {list(read_files)}):
{context[-20000:]} 
(Note: Context truncated for prompt, but full context will be used for generation)

Goal: {user_prompt}

Do you need more files to fully achieve the goal? 
If yes, return a JSON list of NEW file paths.
If no, return an empty JSON list [].
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt_loop)
        ]
        
        response = llm.invoke(messages)
        new_files = extract_json_list(response.content)
        log(f"Round {i+1} - LLM requested additional files: {new_files}")
        
        if not new_files or not isinstance(new_files, list):
            log("No more files needed.")
            break
            
        added_any = False
        for f in new_files:
            if f not in read_files:
                content = read_file_content(repo_path, f)
                if content:
                    if len(context) + len(content) > MAX_CHARS_PER_CALL:
                        log(f"Context limit reached during refinement, skipping {f}")
                        break
                    context += f"\n\n--- File: {f} ---\n{content}"
                    read_files.add(f)
                    added_any = True
        
        if not added_any:
            log("No new files added.")
            break

    # Step 4: Generate Article Directly (V2)
    log("Step 4: Generating article directly (V2 Engine)...")
    log(f"Final Context size: {len(context)} chars")
    
    final_prompt = f"""Context:
{context[:MAX_CHARS_PER_CALL]}

Goal: {user_prompt}

Please write a high-quality technical article based on the context and goal.
Constraints:
1. Strictly control the article length. It MUST be within {word_limit} Chinese characters. Do not exceed this limit.
2. Keep the most important technical details, architecture analysis, and code examples.
3. Ensure the flow is logical and engaging.
4. Use Markdown format.
5. Answer in Chinese.
6. Ensure the content is logically rigorous, semantically smooth, and factually accurate.
7. Maintain a professional perspective, do not exaggerate. Be realistic and rigorous. Avoid words like 'extremely high', 'huge', 'perfect', etc. unless strictly proven. Focus on technical facts.
"""
    log(f"Final Prompt sent to LLM (First 500 chars):\n{final_prompt[:500]}...")
    messages = [
        SystemMessage(content=f"You are a professional technical writer. Answer in Chinese. Your response must be logically rigorous, semantically smooth, and factually accurate. Maintain a professional perspective, do not exaggerate. Be realistic and rigorous. Avoid words like 'extremely high', 'huge', 'perfect', etc. unless strictly proven. Focus on technical facts. Strictly control the length to be within {word_limit} Chinese characters."),
        HumanMessage(content=final_prompt)
    ]
    
    response = llm.invoke(messages)
    final_content = sanitize_mermaid_content(response.content)
    
    # Extract thinking content if available
    thinking_content = ""
    try:
        if hasattr(response, 'additional_kwargs'):
            thinking_content = response.additional_kwargs.get('reasoning_content', '')
            if not thinking_content:
                 # Some providers might put it elsewhere or use different keys
                 thinking_content = response.additional_kwargs.get('thinking', '')
    except Exception as e:
        log(f"Error extracting thinking content: {e}")

    log("Article generated.")

    return {
        "final_content": final_content,
        "detailed_content": "", # No detailed content in V2
        "thinking_content": thinking_content
    }
