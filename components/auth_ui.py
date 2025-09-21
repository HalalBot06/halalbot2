# components/auth_ui.py
"""
Authentication UI components for HalalBot application
Handles login and registration forms with proper Streamlit session state management
"""

import streamlit as st
from core.auth import authenticate_user, register_user


def show_login() -> bool:
    """
    Display login/register interface with proper session state handling
    
    Returns:
        True if user successfully authenticated, False otherwise
    """
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.title("🔐 HalalBot Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login Tab
    with tab1:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", key="login_email_input")
            password = st.text_input("Password", type="password", key="login_password_input")
            login_submitted = st.form_submit_button("Log In")
            
            if login_submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                elif authenticate_user(email, password):
                    st.session_state.authenticated = True
                    st.session_state.email = email
                    # Import here to avoid circular imports
                    from core.auth import is_admin
                    st.session_state.is_admin = is_admin(email)
                    st.success("Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
    
    # Register Tab
    with tab2:
        # Use a form to handle registration cleanly
        with st.form("register_form", clear_on_submit=True):
            new_email = st.text_input("Email", key="register_email_input")
            new_password = st.text_input("Password", type="password", key="register_password_input")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password_input")
            invite_code = st.text_input("Invite Code", key="invite_code_input")
            register_submitted = st.form_submit_button("Register")
            
            if register_submitted:
                # Validation
                if not all([new_email, new_password, confirm_password, invite_code]):
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                else:
                    success, error_msg = register_user(new_email, new_password, invite_code)
                    if success:
                        st.success("Registration successful! Please log in with your new account.")
                        # Switch to login tab by showing a message
                        st.info("👆 Please use the 'Login' tab above to sign in with your new account.")
                    else:
                        st.error(error_msg or "Registration failed.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    return False


def show_logout_button():
    """Display logout button and handle logout"""
    if st.button("Log Out", key="logout_button"):
        # Clear authentication-related session state only
        st.session_state.authenticated = False
        st.session_state.email = ""
        st.session_state.is_admin = False
        
        # Clear any admin-related state
        if "show_admin" in st.session_state:
            del st.session_state.show_admin
            
        st.success("Logged out successfully!")
        st.rerun()


def require_authentication(func):
    """
    Decorator to require authentication for a function
    
    Args:
        func: Function to protect with authentication
        
    Returns:
        Wrapped function that checks authentication
    """
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated", False):
            st.warning("Please log in to access this feature.")
            show_login()
            return None
        return func(*args, **kwargs)
    return wrapper


def require_admin(func):
    """
    Decorator to require admin privileges for a function
    
    Args:
        func: Function to protect with admin requirement
        
    Returns:
        Wrapped function that checks admin status
    """
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated", False):
            st.warning("Please log in to access this feature.")
            show_login()
            return None
        
        if not st.session_state.get("is_admin", False):
            st.error("Admin privileges required for this feature.")
            return None
        
        return func(*args, **kwargs)
    return wrapper


def show_user_info():
    """Display current user information in sidebar"""
    if st.session_state.get("authenticated", False):
        email = st.session_state.get("email", "Unknown")
        is_admin = st.session_state.get("is_admin", False)
        
        user_type = "Admin" if is_admin else "User"
        st.sidebar.info(f"**Logged in as:** {email}\n**Role:** {user_type}")


def init_session_state():
    """Initialize authentication-related session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "email" not in st.session_state:
        st.session_state.email = ""
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "show_admin" not in st.session_state:
        st.session_state.show_admin = False


def check_authentication() -> bool:
    """
    Check if user is authenticated
    
    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get("authenticated", False)


def get_current_user() -> str:
    """
    Get current user's email
    
    Returns:
        User's email if authenticated, empty string otherwise
    """
    if check_authentication():
        return st.session_state.get("email", "")
    return ""


def is_current_user_admin() -> bool:
    """
    Check if current user is admin
    
    Returns:
        True if current user is admin, False otherwise
    """
    return st.session_state.get("is_admin", False)


def clear_form_state():
    """
    Helper function to clear form-related session state if needed
    Only clears non-widget keys to avoid conflicts
    """
    # This function can be used to clear any custom form state
    # that doesn't conflict with widget keys
    form_keys = [key for key in st.session_state.keys()
                 if key.startswith("form_") and not key.endswith("_input")]
    
    for key in form_keys:
        del st.session_state[key]
