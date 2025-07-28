# toast_api/utils/file_utils.py
"""File operation utilities."""
import os
import json
from typing import List, Dict, Any, Optional
from ..utils.logger import logger

def read_text_file(file_path: str) -> Optional[str]:
    """Read a text file and return its contents."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def write_text_file(file_path: str, content: str) -> bool:
    """Write content to a text file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Written to {file_path}")
        return True
    except IOError as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return False

def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Read a JSON file and return parsed data."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"JSON file not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return None

def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Write data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON written to {file_path}")
        return True
    except (IOError, json.JSONEncodeError) as e:
        logger.error(f"Error writing JSON file {file_path}: {e}")
        return False

def read_lines_file(file_path: str) -> Optional[List[str]]:
    """Read a file and return lines as a list."""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        logger.error(f"Error reading lines from {file_path}: {e}")
        return None

def ensure_directory(dir_path: str) -> bool:
    """Ensure a directory exists, create if it doesn't."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except OSError as e:
        logger.error(f"Error creating directory {dir_path}: {e}")
        return False

def file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)

def get_file_size(file_path: str) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None
