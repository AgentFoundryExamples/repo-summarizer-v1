"""
Repository file summary generator.

Analyzes source files to produce deterministic human- and machine-readable summaries
derived solely from filenames, extensions, and paths. No external calls or dynamic
code execution.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


# Language mapping based on file extensions
LANGUAGE_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.jsx': 'JavaScript',
    '.java': 'Java',
    '.go': 'Go',
    '.rs': 'Rust',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.c': 'C',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.ps1': 'PowerShell',
    '.r': 'R',
    '.m': 'Objective-C',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.vue': 'Vue',
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
    '.yml': 'YAML',
    '.yaml': 'YAML',
    '.json': 'JSON',
    '.xml': 'XML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.cfg': 'Config',
    '.conf': 'Config',
}


class FileSummaryError(Exception):
    """Raised when file summary generation fails."""
    pass


def _matches_pattern(filename: str, patterns: List[str]) -> bool:
    """
    Check if a filename matches any of the given patterns.
    
    Args:
        filename: File name to check
        patterns: List of glob-style patterns
    
    Returns:
        True if filename matches any pattern, False otherwise
    """
    for pattern in patterns:
        if pattern.startswith('*'):
            # Suffix matching (e.g., *.py)
            suffix = pattern[1:]
            if filename.endswith(suffix):
                return True
        elif pattern.endswith('*'):
            # Prefix matching (e.g., test*)
            prefix = pattern[:-1]
            if filename.startswith(prefix):
                return True
        else:
            # Exact matching
            if filename == pattern:
                return True
    return False


def _get_language(file_path: Path) -> str:
    """
    Detect language from file extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Language name or 'Unknown'
    """
    extension = file_path.suffix.lower()
    return LANGUAGE_MAP.get(extension, 'Unknown')


def _generate_heuristic_summary(file_path: Path, root_path: Path) -> str:
    """
    Generate a deterministic summary based on filename, path, and extension.
    
    Args:
        file_path: Path to the file
        root_path: Root path of the repository
    
    Returns:
        Summary string
    """
    name = file_path.stem
    extension = file_path.suffix.lower()
    language = _get_language(file_path)
    
    # Get relative path for context
    try:
        rel_path = file_path.relative_to(root_path)
        path_parts = list(rel_path.parent.parts)
    except ValueError:
        path_parts = []
    
    # Heuristics based on filename patterns
    name_lower = name.lower()
    
    # Configuration files
    if name_lower in ['config', 'configuration', 'settings']:
        return f"{language} configuration file"
    
    # Test files
    if name_lower.startswith('test_') or name_lower.endswith('_test') or name_lower.startswith('test'):
        return f"{language} test file"
    
    # Main/entry point files
    if name_lower in ['main', 'index', 'app', '__main__']:
        return f"{language} main entry point"
    
    # CLI files
    if name_lower in ['cli', 'command', 'commands']:
        return f"{language} command-line interface"
    
    # Utility/helper files
    if name_lower in ['utils', 'util', 'utilities', 'helpers', 'helper']:
        return f"{language} utility functions"
    
    # Model files
    if name_lower in ['model', 'models', 'schema', 'schemas']:
        return f"{language} data models"
    
    # Controller/handler files
    if name_lower in ['controller', 'controllers', 'handler', 'handlers']:
        return f"{language} request handlers"
    
    # View/template files
    if name_lower in ['view', 'views', 'template', 'templates']:
        return f"{language} view templates"
    
    # Service files
    if name_lower in ['service', 'services']:
        return f"{language} service layer"
    
    # Repository/DAO files
    if name_lower in ['repository', 'repositories', 'dao']:
        return f"{language} data access layer"
    
    # API files
    if 'api' in name_lower:
        return f"{language} API implementation"
    
    # Database files
    if 'db' in name_lower or 'database' in name_lower:
        return f"{language} database operations"
    
    # Router files
    if 'router' in name_lower or 'routes' in name_lower:
        return f"{language} routing configuration"
    
    # Middleware files
    if 'middleware' in name_lower:
        return f"{language} middleware component"
    
    # Component files (for JS/TS frameworks)
    if extension in ['.jsx', '.tsx', '.vue'] or 'component' in name_lower:
        return f"{language} UI component"
    
    # Package/module initialization
    if name_lower in ['__init__', 'index', 'mod']:
        if 'tests' in path_parts or 'test' in path_parts:
            return f"{language} test module initialization"
        return f"{language} module initialization"
    
    # Path-based heuristics
    if path_parts:
        top_dir = path_parts[0].lower()
        
        if top_dir in ['tests', 'test']:
            return f"{language} test implementation"
        elif top_dir in ['src', 'lib', 'core']:
            return f"{language} core implementation"
        elif top_dir in ['scripts', 'bin']:
            return f"{language} utility script"
        elif top_dir in ['docs', 'documentation']:
            return f"{language} documentation file"
        elif top_dir in ['examples', 'demos', 'samples']:
            return f"{language} example code"
    
    # Default: descriptive summary based on language and name
    # Convert snake_case or kebab-case to words
    words = name.replace('_', ' ').replace('-', ' ')
    
    if language != 'Unknown':
        return f"{language} module for {words}"
    else:
        return f"Source file for {words}"


def scan_files(
    root_path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    exclude_dirs: Optional[Set[str]] = None
) -> List[Path]:
    """
    Scan directory for files matching include patterns and not matching exclude patterns.
    
    Args:
        root_path: Root directory to scan
        include_patterns: List of patterns to include (e.g., ['*.py', '*.js'])
        exclude_patterns: List of patterns to exclude (e.g., ['*.pyc', '*_test.py'])
        exclude_dirs: Set of directory names to skip
    
    Returns:
        List of file paths matching the criteria
    """
    if include_patterns is None:
        include_patterns = []
    if exclude_patterns is None:
        exclude_patterns = []
    if exclude_dirs is None:
        exclude_dirs = set()
    
    matching_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=False):
        # Filter out excluded directories (modifies dirnames in-place)
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        
        # Also filter symlinked directories
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
        
        for filename in sorted(filenames):
            file_path = Path(dirpath) / filename
            
            # Skip symlinks
            if file_path.is_symlink():
                continue
            
            # Check include patterns (if any)
            if include_patterns and not _matches_pattern(filename, include_patterns):
                continue
            
            # Check exclude patterns
            if exclude_patterns and _matches_pattern(filename, exclude_patterns):
                continue
            
            matching_files.append(file_path)
    
    # Sort for deterministic ordering
    return sorted(matching_files)


def generate_file_summaries(
    root_path: Path,
    output_dir: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_dirs: Optional[Set[str]] = None,
    dry_run: bool = False
) -> None:
    """
    Generate file summaries in Markdown and JSON formats.
    
    Args:
        root_path: Root directory to scan
        output_dir: Directory to write output files
        include_patterns: List of patterns to include (e.g., ['*.py', '*.js'])
        exclude_dirs: Set of directory names to skip
        dry_run: If True, only log intent without writing files
    
    Raises:
        FileSummaryError: If file summary generation fails
    """
    try:
        # Scan for matching files
        files = scan_files(root_path, include_patterns, exclude_dirs=exclude_dirs)
        
        if not files:
            if dry_run:
                print("[DRY RUN] No files found matching criteria")
            else:
                print("No files found matching criteria")
            return
        
        # Generate summaries for each file
        summaries = []
        for file_path in files:
            try:
                rel_path = file_path.relative_to(root_path)
            except ValueError:
                # File is outside root_path, use absolute path
                rel_path = file_path
            
            language = _get_language(file_path)
            summary = _generate_heuristic_summary(file_path, root_path)
            
            summaries.append({
                'path': str(rel_path.as_posix()),
                'language': language,
                'summary': summary
            })
        
        # Generate Markdown output
        markdown_lines = ["# File Summaries\n"]
        markdown_lines.append("Heuristic summaries of source files based on filenames, extensions, and paths.\n")
        markdown_lines.append(f"Total files: {len(summaries)}\n")
        
        for entry in summaries:
            markdown_lines.append(f"## {entry['path']}")
            markdown_lines.append(f"**Language:** {entry['language']}  ")
            markdown_lines.append(f"**Summary:** {entry['summary']}\n")
        
        markdown_content = "\n".join(markdown_lines)
        markdown_path = output_dir / "file-summaries.md"
        
        if dry_run:
            print(f"[DRY RUN] Would write file-summaries.md to: {markdown_path}")
            print(f"[DRY RUN] Content length: {len(markdown_content)} bytes")
            print(f"[DRY RUN] Total files: {len(summaries)}")
        else:
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"File summaries written: {markdown_path}")
        
        # Generate JSON output
        json_data = {
            'total_files': len(summaries),
            'files': summaries
        }
        json_path = output_dir / "file-summaries.json"
        
        if dry_run:
            print(f"[DRY RUN] Would write file-summaries.json to: {json_path}")
            print(f"[DRY RUN] JSON entries: {len(summaries)}")
        else:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            print(f"File summaries JSON written: {json_path}")
    
    except Exception as e:
        raise FileSummaryError(f"Failed to generate file summaries: {e}")
