"""
文件类型识别工具
用于区分代码文件和文档文件
"""
import re
from pathlib import Path
from typing import Set, List

# 代码文件扩展名（包含可能包含代码的 Markdown）
CODE_EXTENSIONS: Set[str] = {
    # Python
    '.py', '.pyw', '.pyx',
    # JavaScript/TypeScript
    '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
    # Java
    '.java', '.kt', '.kts',
    # C/C++
    '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx',
    # C#
    '.cs',
    # Go
    '.go',
    # Rust
    '.rs',
    # Ruby
    '.rb', '.erb',
    # PHP
    '.php',
    # Swift
    '.swift',
    # Kotlin
    '.kt', '.ktm',
    # Scala
    '.scala',
    # Shell
    '.sh', '.bash', '.zsh',
    # SQL
    '.sql',
    # HTML/CSS
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    # Vue
    '.vue',
    # React/JSX
    '.jsx',
    # Markdown (可能包含代码，进行代码分析)
    '.md', '.markdown',
    # 配置
    '.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg',
    # Makefile
    'Makefile', 'Dockerfile', '.dockerignore',
    # 脚本
    '.ps1', '.bat', '.cmd',
}

# 纯文档文件扩展名（不包含代码的文件）
DOCUMENT_EXTENSIONS: Set[str] = {
    '.txt', '.text',
    '.doc', '.docx',
    '.rst', '.adoc',
}

# 二进制文件（不分析）
BINARY_EXTENSIONS: Set[str] = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.dylib',
    '.class', '.o', '.obj',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.woff', '.woff2', '.ttf', '.eot',
}


def is_code_file(filename: str) -> bool:
    """
    判断文件是否为代码文件
    
    Args:
        filename: 文件名或文件路径
        
    Returns:
        True 表示代码文件，False 表示非代码文件
    """
    # 获取文件扩展名
    path = Path(filename)
    ext = path.suffix.lower()
    name = path.name.lower()
    
    # 检查是否是 Makefile、Dockerfile 等特殊文件
    if name in ['makefile', 'dockerfile', 'dockerignore', 'gnumakefile']:
        return True
    
    # 检查二进制文件
    if ext in BINARY_EXTENSIONS:
        return False
    
    # 检查代码文件扩展名
    if ext in CODE_EXTENSIONS:
        return True
    
    # 检查是否是配置文件（也算代码）
    if ext in ['.json', '.yaml', '.yml', '.toml', '.xml', '.ini', '.cfg', '.conf']:
        return True
    
    return False


def is_document_file(filename: str) -> bool:
    """
    判断文件是否为文档文件
    
    Args:
        filename: 文件名或文件路径
        
    Returns:
        True 表示文档文件
    """
    path = Path(filename)
    ext = path.suffix.lower()
    
    if ext in DOCUMENT_EXTENSIONS:
        return True
    
    return False


def is_binary_file(filename: str) -> bool:
    """
    判断文件是否为二进制文件
    
    Args:
        filename: 文件名或文件路径
        
    Returns:
        True 表示二进制文件
    """
    path = Path(filename)
    ext = path.suffix.lower()
    
    if ext in BINARY_EXTENSIONS:
        return True
    
    return False


def get_file_category(filename: str) -> str:
    """
    获取文件分类
    
    Args:
        filename: 文件名或文件路径
        
    Returns:
        'code': 代码文件
        'document': 文档文件
        'binary': 二进制文件
        'unknown': 未知类型
    """
    if is_binary_file(filename):
        return 'binary'
    elif is_code_file(filename):
        return 'code'
    elif is_document_file(filename):
        return 'document'
    else:
        return 'unknown'


def filter_code_files(filenames: List[str]) -> List[str]:
    """
    过滤出代码文件
    
    Args:
        filenames: 文件名列表
        
    Returns:
        只有代码文件的列表
    """
    return [f for f in filenames if is_code_file(f)]


def filter_document_files(filenames: List[str]) -> List[str]:
    """
    过滤出文档文件
    
    Args:
        filenames: 文件名列表
        
    Returns:
        只有文档文件的列表
    """
    return [f for f in filenames if is_document_file(f)]


def get_language_from_extension(filename: str) -> str:
    """
    根据文件扩展名获取编程语言
    
    Args:
        filename: 文件名
        
    Returns:
        语言名称，如 'python', 'javascript', 'java' 等
    """
    path = Path(filename)
    ext = path.suffix.lower()
    
    language_map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React JSX',
        '.tsx': 'React TSX',
        '.vue': 'Vue',
        '.java': 'Java',
        '.kt': 'Kotlin',
        '.swift': 'Swift',
        '.go': 'Go',
        '.rs': 'Rust',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C/C++ Header',
        '.hpp': 'C++ Header',
        '.cs': 'C#',
        '.rb': 'Ruby',
        '.php': 'PHP',
        '.scala': 'Scala',
        '.sql': 'SQL',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.ps1': 'PowerShell',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.json': 'JSON',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.xml': 'XML',
        '.toml': 'TOML',
        '.md': 'Markdown',
    }
    
    return language_map.get(ext, 'Unknown')