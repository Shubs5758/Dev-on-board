"""
Utility functions for DevOnboard application.
Handles file operations, language detection, caching, and helper functions.
"""

import os
import hashlib
import re
from pathlib import Path
from typing import Optional


def detect_language(filename: str) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        filename: Name of the file
        
    Returns:
        Language name as string
    """
    ext_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.java': 'Java',
        '.go': 'Go',
        '.rs': 'Rust',
        '.cpp': 'C++',
        '.c': 'C',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.cs': 'C#',
        '.html': 'HTML',
        '.css': 'CSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.md': 'Markdown',
        '.sh': 'Shell',
        '.sql': 'SQL',
        '.r': 'R',
        '.scala': 'Scala',
        '.vue': 'Vue',
    }
    
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, 'Unknown')


def count_lines(content: str) -> int:
    """
    Count non-empty lines in content.
    
    Args:
        content: File content as string
        
    Returns:
        Number of non-empty lines
    """
    if not content:
        return 0
    return len([line for line in content.split('\n') if line.strip()])


def get_repo_hash(repo_url: str) -> str:
    """
    Generate a unique hash for a repository URL for caching.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        MD5 hash of the URL
    """
    return hashlib.md5(repo_url.encode()).hexdigest()[:12]


def is_entry_point(filepath: str) -> bool:
    """
    Check if a file is likely an entry point to the application.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file is an entry point
    """
    filename = Path(filepath).name.lower()
    entry_patterns = [
        'main.py', 'app.py', 'server.py', 'index.js', 'index.ts',
        'main.js', 'main.ts', 'app.js', 'app.ts', 'server.js',
        'server.ts', '__init__.py', 'manage.py', 'run.py',
        'index.html', 'main.go', 'main.java', 'program.cs'
    ]
    return filename in entry_patterns


def is_config_file(filepath: str) -> bool:
    """
    Check if a file is a configuration file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file is a config file
    """
    filename = Path(filepath).name.lower()
    config_patterns = [
        'config', 'settings', '.env', 'package.json', 'requirements.txt',
        'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'tsconfig.json',
        'webpack.config', 'babel.config', 'jest.config', '.eslintrc',
        'docker-compose', 'dockerfile', 'makefile', 'setup.py'
    ]
    return any(pattern in filename for pattern in config_patterns)


def is_test_file(filepath: str) -> bool:
    """
    Check if a file is a test file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        True if file is a test file
    """
    filepath_lower = filepath.lower()
    test_patterns = [
        'test_', '_test.', 'tests/', '/test/', '.test.', '.spec.',
        '__tests__/', 'spec/'
    ]
    return any(pattern in filepath_lower for pattern in test_patterns)


def truncate_for_context(content: str, max_chars: int = 3000) -> str:
    """
    Smart truncation of content preserving function signatures and structure.
    
    Args:
        content: File content to truncate
        max_chars: Maximum characters to keep
        
    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_chars:
        return content
    
    # Try to truncate at a natural boundary (function/class definition)
    lines = content[:max_chars].split('\n')
    
    # Look for the last complete function or class definition
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith(('def ', 'class ', 'function ', 'const ', 'let ', 'var ')):
            truncated = '\n'.join(lines[:i+1])
            return truncated + '\n\n... [truncated for brevity]'
    
    # If no natural boundary found, just truncate
    return content[:max_chars] + '\n\n... [truncated for brevity]'


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 KB", "2.3 MB")
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.1f} MB"


def should_skip_file(filepath: str, repo_root: Optional[str] = None) -> bool:
    """
    Check if a file should be skipped during analysis.
    
    Args:
        filepath: Path to the file
        repo_root: Optional repository root to evaluate relative paths
        
    Returns:
        True if file should be skipped
    """
    if repo_root:
        try:
            filepath = os.path.relpath(filepath, repo_root)
        except ValueError:
            pass

    skip_patterns = [
        'node_modules/', '.git/', '__pycache__/', 'dist/', 'build/',
        'vendor/', '.venv/', 'venv/', 'env/', '.pytest_cache/',
        '.mypy_cache/', '.tox/', 'coverage/', '.coverage',
        '.DS_Store', 'thumbs.db', '.idea/', '.vscode/',
        'target/', 'bin/', 'obj/', 'out/', 'pkg/',
        '.next/', '.nuxt/', '.cache/'
    ]
    
    filepath_lower = filepath.replace('\\', '/').lower()
    return any(pattern in filepath_lower for pattern in skip_patterns)


def should_skip_extension(filename: str) -> bool:
    """
    Check if a file extension should be skipped.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if extension should be skipped
    """
    skip_extensions = [
        '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
        '.exe', '.bin', '.dat', '.db', '.sqlite', '.sqlite3',
        '.log', '.lock', '.pid', '.swp', '.swo', '.bak',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.mp3', '.mp4', '.avi', '.mov', '.wav',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.min.js', '.min.css', '.map'
    ]
    
    ext = Path(filename).suffix.lower()
    return ext in skip_extensions


def extract_repo_name(repo_url: str) -> str:
    """
    Extract repository name from GitHub URL.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Repository name
    """
    # Remove trailing slash and .git
    url = repo_url.rstrip('/').replace('.git', '')
    
    # Extract name from URL
    parts = url.split('/')
    if len(parts) >= 2:
        return parts[-1]
    return "unknown-repo"


def is_valid_github_url(url: str) -> bool:
    """
    Validate if URL is a valid GitHub repository URL.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid GitHub URL
    """
    # Remove query parameters and fragments
    url = url.strip().split('?')[0].split('#')[0]
    
    github_patterns = [
        r'^https?://github\.com/[\w-]+/[\w.-]+/?$',
        r'^https?://www\.github\.com/[\w-]+/[\w.-]+/?$',
        r'^git@github\.com:[\w-]+/[\w.-]+\.git$'
    ]
    
    return any(re.match(pattern, url) for pattern in github_patterns)


def get_role_keywords(role: str) -> list:
    """
    Get relevant keywords for a developer role.
    
    Args:
        role: Developer role
        
    Returns:
        List of relevant keywords
    """
    role_keywords = {
        "Frontend Developer": [
            'component', 'ui', 'view', 'template', 'style', 'css', 'html',
            'react', 'vue', 'angular', 'jsx', 'tsx', 'dom', 'render',
            'state', 'props', 'hook', 'router', 'navigation'
        ],
        "Backend Developer": [
            'api', 'route', 'controller', 'service', 'model', 'database',
            'schema', 'query', 'middleware', 'auth', 'server', 'endpoint',
            'handler', 'repository', 'dao', 'orm', 'sql', 'rest', 'graphql'
        ],
        "Full-Stack Developer": [
            'api', 'component', 'route', 'service', 'model', 'view',
            'controller', 'middleware', 'database', 'ui', 'auth'
        ],
        "DevOps Engineer": [
            'docker', 'kubernetes', 'ci', 'cd', 'pipeline', 'deploy',
            'config', 'infrastructure', 'terraform', 'ansible', 'jenkins',
            'github actions', 'gitlab', 'monitoring', 'logging', 'nginx'
        ],
        "ML/Data Engineer": [
            'model', 'train', 'data', 'pipeline', 'feature', 'dataset',
            'ml', 'ai', 'neural', 'tensor', 'numpy', 'pandas', 'sklearn',
            'pytorch', 'tensorflow', 'transform', 'predict', 'inference'
        ],
        "General / Explore": [
            'main', 'app', 'core', 'util', 'helper', 'config', 'init'
        ]
    }
    
    return role_keywords.get(role, role_keywords["General / Explore"])


def calculate_role_relevance(filepath: str, content: str, role: str) -> float:
    """
    Calculate how relevant a file is to a specific role (0.0 to 1.0).
    
    Args:
        filepath: Path to the file
        content: File content
        role: Developer role
        
    Returns:
        Relevance score between 0.0 and 1.0
    """
    keywords = get_role_keywords(role)
    filepath_lower = filepath.lower()
    content_lower = content.lower()
    
    score = 0.0
    
    # Check filepath
    for keyword in keywords:
        if keyword in filepath_lower:
            score += 0.3
    
    # Check content
    keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
    score += min(keyword_count * 0.1, 0.7)
    
    # Boost for entry points
    if is_entry_point(filepath):
        score += 0.2
    
    # Boost for config files (important for DevOps)
    if is_config_file(filepath) and role == "DevOps Engineer":
        score += 0.3
    
    return min(score, 1.0)

# Made with Bob
