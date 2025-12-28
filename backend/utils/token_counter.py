import os

def count_tokens_in_dir(directory: str) -> int:
    """
    Estimate token count for a directory by counting characters in source files.
    1 token approx 4 chars.
    """
    if not os.path.exists(directory):
        return 0

    total_chars = 0
    # Extensions to include
    extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp', 
        '.md', '.txt', '.json', '.yml', '.yaml', '.html', '.css', '.go', '.rs', 
        '.php', '.rb', '.sh', '.sql', '.xml', '.vue'
    }
    
    # Dirs to exclude
    exclude_dirs = {
        '.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', 
        '.idea', '.vscode', 'target', 'bin', 'obj'
    }

    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in extensions:
                file_path = os.path.join(root, file)
                try:
                    # Try reading as utf-8, ignore errors if binary/mixed
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        total_chars += len(content)
                except Exception:
                    pass
                    
    # Estimate tokens: chars / 4
    return int(total_chars / 4)
