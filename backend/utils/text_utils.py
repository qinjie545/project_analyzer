import re

def sanitize_mermaid_content(text: str) -> str:
    """
    Replace Chinese quotes with English quotes in mermaid blocks.
    
    Args:
        text: The markdown content to sanitize.
        
    Returns:
        The sanitized markdown content.
    """
    if not text:
        return ""
        
    pattern = r'(```mermaid\s*[\s\S]*?```)'
    
    def replace_quotes(match):
        content = match.group(1)
        return content.replace('“', '"').replace('”', '"')
        
    return re.sub(pattern, replace_quotes, text)
