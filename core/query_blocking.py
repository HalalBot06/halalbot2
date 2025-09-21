# core/query_blocking.py
"""
Query blocking and filtering system for HalalBot application
Handles inappropriate query detection and content filtering
"""

from typing import List, Set
from utils.file_operations import load_text_file_lines, append_jsonl
from utils.logging import log_blocked_query


# File paths
BLOCKED_FILE = "blocked_queries.txt"


def load_blocked_phrases() -> List[str]:
    """
    Load blocked phrases from file
    
    Returns:
        List of blocked phrases (lowercase)
    """
    phrases = load_text_file_lines(BLOCKED_FILE)
    return [phrase.lower() for phrase in phrases]


def is_blocked_query(query: str, blocked_phrases: List[str] = None) -> bool:
    """
    Check if a query contains blocked content
    
    Args:
        query: Query text to check
        blocked_phrases: List of blocked phrases (loads from file if None)
        
    Returns:
        True if query should be blocked, False otherwise
    """
    if blocked_phrases is None:
        blocked_phrases = load_blocked_phrases()
    
    query_lower = query.lower()
    return any(phrase in query_lower for phrase in blocked_phrases)


def add_blocked_phrase(phrase: str) -> bool:
    """
    Add a new phrase to the blocked list
    
    Args:
        phrase: Phrase to block
        
    Returns:
        True if added successfully, False otherwise
    """
    try:
        with open(BLOCKED_FILE, "a", encoding="utf-8") as f:
            f.write(phrase.strip() + "\n")
        return True
    except IOError:
        return False


def remove_blocked_phrase(phrase: str) -> bool:
    """
    Remove a phrase from the blocked list
    
    Args:
        phrase: Phrase to remove
        
    Returns:
        True if removed successfully, False otherwise
    """
    phrases = load_text_file_lines(BLOCKED_FILE)
    
    # Filter out the phrase to remove (case-insensitive)
    filtered_phrases = [p for p in phrases if p.lower() != phrase.lower()]
    
    # Only update if we actually removed something
    if len(filtered_phrases) < len(phrases):
        try:
            with open(BLOCKED_FILE, "w", encoding="utf-8") as f:
                for phrase in filtered_phrases:
                    f.write(phrase + "\n")
            return True
        except IOError:
            return False
    
    return False


def get_blocked_phrases() -> List[str]:
    """
    Get all currently blocked phrases
    
    Returns:
        List of blocked phrases
    """
    return load_text_file_lines(BLOCKED_FILE)


def validate_and_log_query(email: str, query: str) -> bool:
    """
    Validate a query and log if blocked
    
    Args:
        email: User's email address
        query: Query to validate
        
    Returns:
        True if query is allowed, False if blocked
    """
    if is_blocked_query(query):
        log_blocked_query(email, query)
        return False
    
    return True


class QueryFilter:
    """
    Advanced query filtering class with caching and custom rules
    """
    
    def __init__(self):
        self._blocked_phrases = None
        self._custom_rules = []
    
    def _load_blocked_phrases(self) -> List[str]:
        """Load and cache blocked phrases"""
        if self._blocked_phrases is None:
            self._blocked_phrases = load_blocked_phrases()
        return self._blocked_phrases
    
    def add_custom_rule(self, rule_func):
        """
        Add a custom filtering rule function
        
        Args:
            rule_func: Function that takes a query string and returns bool
                      (True if should be blocked)
        """
        self._custom_rules.append(rule_func)
    
    def is_query_blocked(self, query: str) -> bool:
        """
        Check if query should be blocked using all rules
        
        Args:
            query: Query to check
            
    Returns:
            True if query should be blocked
        """
        # Check against blocked phrases
        if is_blocked_query(query, self._load_blocked_phrases()):
            return True
        
        # Check custom rules
        for rule in self._custom_rules:
            try:
                if rule(query):
                    return True
            except Exception:
                # If rule fails, continue with other rules
                continue
        
        return False
    
    def refresh_phrases(self):
        """Refresh cached blocked phrases from file"""
        self._blocked_phrases = None


# Global filter instance
_global_filter = QueryFilter()


def get_query_filter() -> QueryFilter:
    """Get the global query filter instance"""
    return _global_filter


# Example custom rules that could be added:

def rule_excessive_caps(query: str) -> bool:
    """Block queries with excessive capitalization"""
    if len(query) < 10:
        return False
    caps_ratio = sum(1 for c in query if c.isupper()) / len(query)
    return caps_ratio > 0.7


def rule_excessive_repetition(query: str) -> bool:
    """Block queries with excessive character repetition"""
    words = query.split()
    for word in words:
        if len(word) > 5:
            # Check for repeated characters
            for i in range(len(word) - 2):
                if word[i] == word[i+1] == word[i+2]:
                    return True
    return False


def rule_too_short(query: str) -> bool:
    """Block queries that are too short to be meaningful"""
    return len(query.strip()) < 3


def setup_default_rules():
    """Setup default filtering rules"""
    filter_instance = get_query_filter()
    filter_instance.add_custom_rule(rule_excessive_caps)
    filter_instance.add_custom_rule(rule_excessive_repetition)
    filter_instance.add_custom_rule(rule_too_short)