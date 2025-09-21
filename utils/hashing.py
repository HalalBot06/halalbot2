# utils/hashing.py
"""
Hashing utilities for HalalBot application
Provides secure hashing for passwords, emails, and text content
"""

import hashlib


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256
    
    Args:
        password: Plain text password
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def hash_email(email: str) -> str:
    """
    Hash an email address for file naming and privacy
    
    Args:
        email: Email address to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(email.encode()).hexdigest()


def hash_text(text: str) -> str:
    """
    Hash arbitrary text content for identification
    
    Args:
        text: Text content to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password: Plain text password to verify
        hashed_password: Stored hash to compare against
        
    Returns:
        True if password matches hash, False otherwise
    """
    return hash_password(password) == hashed_password