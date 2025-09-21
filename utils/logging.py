# utils/logging.py
"""
Logging utilities for HalalBot application
Handles query history, blocked queries, and user activity logging
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from .file_operations import append_jsonl, ensure_directory
from .hashing import hash_email


# Default file paths
HISTORY_DIR = "data/history"
BLOCKED_LOG = "blocked_queries_log.jsonl"
FEEDBACK_LOG_FILE = "feedback_log.jsonl"

# Ensure history directory exists
ensure_directory(HISTORY_DIR)


def log_query_for_user(email: str, query: str, results: List[Dict[str, Any]]) -> bool:
    """
    Log a search query and its results for a specific user
    
    Args:
        email: User's email address
        query: Search query text
        results: List of search results
        
    Returns:
        True if logged successfully, False otherwise
    """
    user_hash = hash_email(email)
    file_path = os.path.join(HISTORY_DIR, f"{user_hash}.jsonl")
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "results": results,
        "result_count": len(results)
    }
    
    return append_jsonl(file_path, entry)


def log_blocked_query(email: str, query: str) -> bool:
    """
    Log a blocked query attempt
    
    Args:
        email: User's email address
        query: Blocked query text
        
    Returns:
        True if logged successfully, False otherwise
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "email": email,
        "query": query,
        "type": "blocked_query"
    }
    
    return append_jsonl(BLOCKED_LOG, entry)


def log_feedback(query: str, text: str, vote: str, user_email: Optional[str] = None) -> bool:
    """
    Log user feedback on search results
    
    Args:
        query: Original search query
        text: Text content that was rated
        vote: "up" or "down"
        user_email: User's email (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    from .hashing import hash_text
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "text_hash": hash_text(text),
        "vote": vote,
        "user": user_email or "anonymous"
    }
    
    return append_jsonl(FEEDBACK_LOG_FILE, entry)


def log_user_activity(email: str, activity_type: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """
    Log general user activity
    
    Args:
        email: User's email address
        activity_type: Type of activity (login, search, feedback, etc.)
        details: Additional activity details
        
    Returns:
        True if logged successfully, False otherwise
    """
    user_hash = hash_email(email)
    file_path = os.path.join(HISTORY_DIR, f"{user_hash}_activity.jsonl")
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "activity_type": activity_type,
        "details": details or {}
    }
    
    return append_jsonl(file_path, entry)


def get_user_query_count(email: str, days: int = 30) -> int:
    """
    Get the number of queries a user has made in the last N days
    
    Args:
        email: User's email address
        days: Number of days to look back
        
    Returns:
        Count of queries in the specified period
    """
    from datetime import timedelta
    import json
    
    user_hash = hash_email(email)
    file_path = os.path.join(HISTORY_DIR, f"{user_hash}.jsonl")
    
    if not os.path.exists(file_path):
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days)
    count = 0
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time >= cutoff_date:
                        count += 1
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
    except IOError:
        pass
    
    return count