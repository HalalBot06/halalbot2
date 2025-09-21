# core/invite_codes.py
"""
Invite code management for HalalBot application
Handles creation, validation, and usage of invite codes
"""

import secrets
import string
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from utils.file_operations import load_json, save_json


# File paths
INVITE_CODES_FILE = "invite_codes.json"


def load_invite_codes() -> dict:
    """Load invite codes from JSON file"""
    return load_json(INVITE_CODES_FILE)


def save_invite_codes(codes: dict) -> bool:
    """Save invite codes to JSON file"""
    return save_json(INVITE_CODES_FILE, codes)


def validate_invite_code(code: str) -> bool:
    """
    Check if an invite code is valid and unused
    
    Args:
        code: Invite code to validate
        
    Returns:
        True if code is valid and unused, False otherwise
    """
    codes = load_invite_codes()
    return code in codes and not codes[code].get("used", False)


def use_invite_code(code: str, email: str) -> bool:
    """
    Mark an invite code as used
    
    Args:
        code: Invite code to mark as used
        email: Email of the user who used the code
        
    Returns:
        True if successfully marked as used, False otherwise
    """
    codes = load_invite_codes()
    
    if code not in codes:
        return False
    
    codes[code]["used"] = True
    codes[code]["email"] = email
    codes[code]["used_at"] = datetime.now().isoformat()
    
    return save_invite_codes(codes)


def generate_invite_code(length: int = 8) -> str:
    """
    Generate a random invite code
    
    Args:
        length: Length of the code to generate
        
    Returns:
        Random alphanumeric invite code
    """
    characters = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def create_invite_code(code: Optional[str] = None, description: str = "") -> Tuple[bool, str]:
    """
    Create a new invite code
    
    Args:
        code: Specific code to create (if None, generates random)
        description: Optional description for the code
        
    Returns:
        Tuple of (success: bool, code: str)
    """
    codes = load_invite_codes()
    
    # Generate code if not provided
    if code is None:
        code = generate_invite_code()
        # Ensure uniqueness
        while code in codes:
            code = generate_invite_code()
    
    # Check if code already exists
    if code in codes:
        return False, f"Code '{code}' already exists"
    
    # Create new code entry
    codes[code] = {
        "used": False,
        "created_at": datetime.now().isoformat(),
        "description": description,
        "email": None,
        "used_at": None
    }
    
    if save_invite_codes(codes):
        return True, code
    else:
        return False, "Failed to save invite code"


def create_multiple_invite_codes(count: int, prefix: str = "") -> List[str]:
    """
    Create multiple invite codes at once
    
    Args:
        count: Number of codes to create
        prefix: Optional prefix for the codes
        
    Returns:
        List of created invite codes
    """
    created_codes = []
    
    for i in range(count):
        code = f"{prefix}{generate_invite_code()}" if prefix else generate_invite_code()
        success, result_code = create_invite_code(code)
        
        if success:
            created_codes.append(result_code)
    
    return created_codes


def get_invite_code_stats() -> Dict[str, int]:
    """
    Get statistics about invite codes
    
    Returns:
        Dictionary with invite code statistics
    """
    codes = load_invite_codes()
    
    total = len(codes)
    used = sum(1 for code_data in codes.values() if code_data.get("used", False))
    unused = total - used
    
    return {
        "total": total,
        "used": used,
        "unused": unused
    }


def get_invite_code_info(code: str) -> Optional[dict]:
    """
    Get information about a specific invite code
    
    Args:
        code: Invite code to look up
        
    Returns:
        Code information dictionary or None if not found
    """
    codes = load_invite_codes()
    return codes.get(code)


def list_unused_invite_codes() -> List[str]:
    """
    Get list of all unused invite codes
    
    Returns:
        List of unused invite codes
    """
    codes = load_invite_codes()
    return [code for code, data in codes.items() if not data.get("used", False)]


def list_used_invite_codes() -> List[Dict[str, str]]:
    """
    Get list of all used invite codes with usage info
    
    Returns:
        List of dictionaries with code usage information
    """
    codes = load_invite_codes()
    used_codes = []
    
    for code, data in codes.items():
        if data.get("used", False):
            used_codes.append({
                "code": code,
                "email": data.get("email", "Unknown"),
                "used_at": data.get("used_at", "Unknown"),
                "description": data.get("description", "")
            })
    
    return used_codes


def delete_invite_code(code: str) -> bool:
    """
    Delete an invite code
    
    Args:
        code: Invite code to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    codes = load_invite_codes()
    
    if code not in codes:
        return False
    
    del codes[code]
    return save_invite_codes(codes)