# app.py
"""
HalalBot - Islamic Knowledge Chatbot
Refactored main application file with modular architecture

This is the main entry point for the HalalBot Streamlit application.
All business logic has been extracted to separate modules for better
maintainability and scalability.
"""

# --- SECTION 1: IMPORTS & DEPENDENCIES ---
import streamlit as st

# Component imports
from components.styling import apply_custom_css, apply_page_config
from components.auth_ui import (
    show_login, init_session_state, check_authentication, 
    show_logout_button, show_user_info
)
from components.search_ui import create_search_interface
from components.admin_ui import show_admin_dashboard, show_admin_tools_sidebar

# Core logic imports
from core.query_blocking import setup_default_rules

# Utils
from utils.file_operations import ensure_directory


# --- SECTION 2: APPLICATION CONFIGURATION ---
def configure_app():
    """Configure Streamlit app settings and initialize components"""
    # Set page configuration
    apply_page_config()
    
    # Apply custom CSS styling
    apply_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Setup query filtering rules
    setup_default_rules()
    
    # Ensure required directories exist
    ensure_directory("data/history")
    ensure_directory("static")


# --- SECTION 3: MAIN APPLICATION ROUTING ---
def main():
    """Main application entry point with clean routing logic"""
    
    # Configure the application
    configure_app()
    
    # Check authentication status
    if not check_authentication():
        # Show login interface if not authenticated
        show_login()
        return
    
    # User is authenticated - show main interface
    show_authenticated_interface()


def show_authenticated_interface():
    """Display the main interface for authenticated users"""
    
    # Show user info in sidebar
    show_user_info()
    
    # Show admin tools in sidebar if user is admin
    show_admin_tools_sidebar()
    
    # Main content area
    main_content_area()
    
    # Logout button
    st.markdown("---")
    show_logout_button()


# --- SECTION 4: MAIN CONTENT INTERFACE ---
def main_content_area():
    """Handle the main content area with search and admin sections"""
    
    # Check if admin dashboard should be shown
    if st.session_state.get("show_admin", False):
        show_admin_dashboard()
        
        # Button to return to search
        if st.button("🔍 Back to Search"):
            st.session_state.show_admin = False
            st.rerun()
    else:
        # Show main search interface
        create_search_interface()
        
        # Show admin section for admin users
        from components.auth_ui import is_current_user_admin
        if is_current_user_admin():
            st.markdown("---")
            if st.button("🛠️ Admin Dashboard"):
                st.session_state.show_admin = True
                st.rerun()


# --- SECTION 5: ERROR HANDLING & DEBUGGING ---
def handle_app_errors():
    """Global error handler for the application"""
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh the page.")
        
        # Show error details in expander for debugging
        with st.expander("🐛 Error Details (for debugging)"):
            st.exception(e)
        
        # Log error (you could expand this to use proper logging)
        print(f"Application error: {e}")


# --- SECTION 6: DEVELOPMENT & TESTING HELPERS ---
def show_dev_info():
    """Show development information in sidebar (only in debug mode)"""
    if st.sidebar.checkbox("🔧 Debug Mode", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("🐛 Debug Info")
        
        # Session state info
        with st.sidebar.expander("Session State"):
            st.write(st.session_state)
        
        # App info
        st.sidebar.write(f"**App Version:** Alpha v0.2")
        st.sidebar.write(f"**Architecture:** Modular")


# --- SECTION 7: APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    # Add development helpers in debug mode
    # if st.secrets.get("DEBUG_MODE", False):
    #   show_dev_info()
    
    # Run the application with error handling
    handle_app_errors()

