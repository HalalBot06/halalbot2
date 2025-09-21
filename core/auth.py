# core/auth.py
"""
Authentication core logic for HalalBot application
Handles user authentication, registration, and session management
"""

from typing import Tuple, Optional
from utils.file_operations import load_json, save_json
from utils.hashing import hash_password, verify_password
from .invite_codes import validate_invite_code, use_invite_code


# File paths
USERS_FILE = "users.json"


def load_users() -> dict:
    """Load users from JSON file"""
    return load_json(USERS_FILE)


def save_users(users: dict) -> bool:
    """Save users to JSON file"""
    return save_json(USERS_FILE, users)


def authenticate_user(email: str, password: str) -> bool:
    """
    Authenticate a user with email and password
    
    Args:
        email: User's email address
        password: Plain text password
        
    Returns:
        True if authentication successful, False otherwise
    """
    users = load_users()
    
    if email not in users:
        return False
    
    stored_hash = users[email].get("password", "")
    return verify_password(password, stored_hash)


def register_user(email: str, password: str, invite_code: str) -> Tuple[bool, Optional[str]]:
    """
    Register a new user
    
    Args:
        email: User's email address
        password: Plain text password
        invite_code: Invite code for registration
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    users = load_users()
    
    # Check if user already exists
    if email in users:
        return False, "User already exists."
    
    # Validate invite code
    if not validate_invite_code(invite_code):
        return False, "Invalid or used invite code."
    
    # Create new user
    users[email] = {
        "password": hash_password(password),
        "invite_code": invite_code,
        "is_admin": False,
        "created_at": None,  # Can be set to current timestamp if needed
        "last_login": None
    }
    
    # Save users and mark invite code as used
    if save_users(users):
        use_invite_code(invite_code, email)
        return True, None
    else:
        return False, "Failed to save user data."


def is_admin(email: str) -> bool:
    """
    Check if a user has admin privileges
    
    Args:
        email: User's email address
        
    Returns:
        True if user is admin, False otherwise
    """
    users = load_users()
    return users.get(email, {}).get("is_admin", False)


def get_user_info(email: str) -> Optional[dict]:
    """
    Get user information
    
    Args:
        email: User's email address
        
    Returns:
        User info dictionary or None if user doesn't exist
    """
    users = load_users()
    user_data = users.get(email)
    
    if user_data:
        # Return copy without password for security
        safe_data = user_data.copy()
        safe_data.pop("password", None)
        return safe_data
    
    return None


def update_user_admin_status(email: str, is_admin_status: bool) -> bool:
    """
    Update a user's admin status
    
    Args:
        email: User's email address
        is_admin_status: New admin status
        
    Returns:
        True if updated successfully, False otherwise
    """
    users = load_users()
    
    if email not in users:
        return False
    
    users[email]["is_admin"] = is_admin_status
    return save_users(users)


def change_user_password(email: str, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Change a user's password
    
    Args:
        email: User's email address
        old_password: Current password for verification
        new_password: New password to set
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    # Verify current password
    if not authenticate_user(email, old_password):
        return False, "Current password is incorrect."
    
    users = load_users()
    users[email]["password"] = hash_password(new_password)
    
    if save_users(users):
        return True, None
    else:
        return False, "Failed to save new password."


def get_user_count() -> int:
    """
    Get total number of registered users
    
    Returns:
        Number of registered users
    """
    users = load_users()
    return len(users)


def get_admin_count() -> int:
    """
    Get number of admin users
    
    Returns:
        Number of admin users
    """
    users = load_users()
    return sum(1 for user in users.values() if user.get("is_admin", False))