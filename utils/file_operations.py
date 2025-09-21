# utils/file_operations.py
"""
File I/O utilities for HalalBot application
Handles JSON file operations and directory management
"""

import json
import os
from typing import Dict, Any, Optional


def load_json(filepath: str) -> Dict[str, Any]:
    """
    Load JSON data from file with error handling
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Dictionary containing JSON data, empty dict if file doesn't exist
    """
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON from {filepath}: {e}")
        return {}


def save_json(filepath: str, data: Dict[str, Any]) -> bool:
    """
    Save data to JSON file with error handling
    
    Args:
        filepath: Path to save JSON file
        data: Dictionary to save as JSON
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists (only if filepath has a directory)
        directory = os.path.dirname(filepath)
        if directory:  # Only create directory if it's not empty
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving JSON to {filepath}: {e}")
        return False


def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        directory: Directory path to create
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {directory}: {e}")
        return False


def load_text_file_lines(filepath: str) -> list[str]:
    """
    Load lines from a text file, filtering empty lines
    
    Args:
        filepath: Path to text file
        
    Returns:
        List of non-empty lines from the file
    """
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        print(f"Error loading text file {filepath}: {e}")
        return []


def append_jsonl(filepath: str, data: Dict[str, Any]) -> bool:
    """
    Append a JSON object as a new line to a JSONL file
    
    Args:
        filepath: Path to JSONL file
        data: Dictionary to append as JSON line
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists (only if filepath has a directory)
        directory = os.path.dirname(filepath)
        if directory:  # Only create directory if it's not empty
            os.makedirs(directory, exist_ok=True)
        
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return True
    except (IOError, TypeError) as e:
        print(f"Error appending to JSONL file {filepath}: {e}")
        return False
