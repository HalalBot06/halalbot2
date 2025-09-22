# app.py
"""
HalalBot - Islamic Knowledge Chatbot
Enhanced with Conversational AI Interface

MAJOR UPDATE: Added conversational interface option
Toggle between traditional search and conversational AI
"""

# --- SECTION 1: IMPORTS & DEPENDENCIES ---
import streamlit as st
import os
from pathlib import Path
import sys

# Component imports
from components.styling import (
    apply_custom_css, apply_page_config, load_static_assets, test_static_files
)
from components.auth_ui import (
    show_login, init_session_state, check_authentication,
    show_logout_button, show_user_info
)

# UPDATED: Import both search interfaces
from components.search_ui import create_search_interface  # Original
from components.conversational_search_ui import create_conversational_search_interface  # NEW

from components.admin_ui import show_admin_dashboard, show_admin_tools_sidebar

# Core logic imports
from core.query_blocking import setup_default_rules

# Utils
from utils.file_operations import ensure_directory


# --- SECTION 2: RAILWAY DEPLOYMENT FIXES ---
def setup_railway_environment():
    """Setup environment variables and paths for Railway deployment"""
    
    # Set PORT if not set (Railway requirement)
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '8080'
    
    # Ensure static directory exists
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # Check if we're running on Railway
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    
    if is_railway:
        print("🚄 Running on Railway deployment")
        # Railway-specific setup
        setup_railway_static_files()
    else:
        print("🏠 Running locally")
    
    return is_railway


def setup_railway_static_files():
    """Setup static file handling for Railway deployment"""
    
    # Test static file access
    print("🔍 Testing static file access on Railway...")
    logo_exists, favicon_exists = test_static_files()
    
    if not logo_exists or not favicon_exists:
        print("⚠️ Some static files missing, creating fallbacks...")
        create_fallback_assets()


def create_fallback_assets():
    """Create fallback assets if original files are missing"""
    
    # This function would create minimal fallback images if needed
    # For now, we'll rely on the CSS fallbacks
    pass


# --- SECTION 3: APPLICATION CONFIGURATION ---
def configure_app():
    """Configure Streamlit app settings and initialize components"""
    
    # CRITICAL: Apply page config FIRST, before any other Streamlit calls
    apply_page_config()
    
    # Setup Railway environment
    setup_railway_environment()
    
    # Load static assets
    assets = load_static_assets()
    
    # CRITICAL: Apply custom CSS AFTER page config but BEFORE any UI elements
    apply_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # NEW: Initialize conversational interface preference
    init_conversational_preferences()
    
    # Setup query filtering rules
    setup_default_rules()
    
    # Ensure required directories exist
    ensure_directory("data/history")
    
    # Debug info for deployment
    if st.sidebar.checkbox("🔧 Debug Info", False):
        show_debug_info(assets)


def init_conversational_preferences():
    """Initialize user preferences for conversational interface"""
    
    if 'use_conversational_interface' not in st.session_state:
        # Default to conversational interface for new users
        st.session_state.use_conversational_interface = True
    
    if 'interface_onboarding_shown' not in st.session_state:
        st.session_state.interface_onboarding_shown = False


def show_debug_info(assets):
    """Show debug information for troubleshooting"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Debug Info")
    
    # Environment info
    st.sidebar.write("**Environment:**")
    st.sidebar.write(f"Railway: {os.environ.get('RAILWAY_ENVIRONMENT', 'No')}")
    st.sidebar.write(f"Port: {os.environ.get('PORT', 'Not set')}")
    st.sidebar.write(f"Working dir: {os.getcwd()}")
    
    # Asset loading status
    st.sidebar.write("**Assets:**")
    st.sidebar.write(f"Logo loaded: {'✅' if assets.get('logo') else '❌'}")
    st.sidebar.write(f"Favicon loaded: {'✅' if assets.get('favicon') else '❌'}")
    
    # Interface status
    st.sidebar.write("**Interface:**")
    interface_type = "Conversational" if st.session_state.use_conversational_interface else "Traditional"
    st.sidebar.write(f"Mode: {interface_type}")
    
    # File system check
    st.sidebar.write("**File System:**")
    st.sidebar.write(f"Static dir exists: {'✅' if os.path.exists('static') else '❌'}")
    if os.path.exists('static'):
        static_files = os.listdir('static')
        st.sidebar.write(f"Static files: {static_files}")


# --- SECTION 4: MAIN APPLICATION ROUTING ---
def main():
    """Main application entry point with clean routing logic"""
    
    try:
        # Configure the application (this includes CSS application)
        configure_app()
        
        # Check authentication status
        if not check_authentication():
            # Show login interface if not authenticated
            show_login()
            return
        
        # User is authenticated - show main interface
        show_authenticated_interface()
        
    except Exception as e:
        st.error("⚠️ Application configuration error. Please refresh the page.")
        
        # Show error details in expander for debugging
        with st.expander("🐛 Error Details"):
            st.exception(e)


def show_authenticated_interface():
    """Display the main interface for authenticated users"""
    
    # Show user info in sidebar
    show_user_info()
    
    # NEW: Show interface toggle in sidebar
    show_interface_toggle()
    
    # Show admin tools in sidebar if user is admin
    show_admin_tools_sidebar()
    
    # Main content area
    main_content_area()
    
    # Logout button
    st.markdown("---")
    show_logout_button()


def show_interface_toggle():
    """Show interface mode toggle in sidebar"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔄 Interface Mode")
    
    # Toggle between interfaces
    use_conversational = st.sidebar.toggle(
        "Conversational AI Mode",
        value=st.session_state.use_conversational_interface,
        help="Toggle between traditional search and conversational AI interface"
    )
    
    # Update session state if changed
    if use_conversational != st.session_state.use_conversational_interface:
        st.session_state.use_conversational_interface = use_conversational
        st.rerun()
    
    # Show current mode
    if st.session_state.use_conversational_interface:
        st.sidebar.success("🤖 AI Chat Mode Active")
        st.sidebar.caption("Natural conversation with Islamic AI assistant")
    else:
        st.sidebar.info("🔍 Traditional Search Mode")
        st.sidebar.caption("Direct search through Islamic texts")


# --- SECTION 5: MAIN CONTENT INTERFACE ---
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
        # NEW: Choose interface based on user preference
        show_search_interface()
        
        # Show admin section for admin users
        from components.auth_ui import is_current_user_admin
        if is_current_user_admin():
            st.markdown("---")
            if st.button("🛠️ Admin Dashboard"):
                st.session_state.show_admin = True
                st.rerun()


def show_search_interface():
    """Show the appropriate search interface based on user preference"""
    
    # Show onboarding message for first-time conversational users
    if (st.session_state.use_conversational_interface and
        not st.session_state.interface_onboarding_shown):
        show_conversational_onboarding()
    
    try:
        if st.session_state.use_conversational_interface:
            # NEW: Use conversational interface
            create_conversational_search_interface()
        else:
            # ORIGINAL: Use traditional search interface
            create_search_interface()
            
    except ImportError as e:
        # Fallback if conversational interface isn't available
        st.warning("⚠️ Conversational interface not available. Using traditional search.")
        st.session_state.use_conversational_interface = False
        create_search_interface()
        
        # Show error in debug mode
        if st.session_state.get("debug_mode", False):
            st.error(f"Import error: {e}")
    
    except Exception as e:
        st.error("❌ Error loading search interface. Please refresh the page.")
        if st.session_state.get("debug_mode", False):
            st.exception(e)


def show_conversational_onboarding():
    """Show onboarding message for new conversational interface users"""
    
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #E6FFFA 0%, #B2F5EA 100%);
            border: 2px solid #38B2AC;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        ">
            <h3 style="color: #1A365D; margin: 0 0 1rem 0;">
                🆕 Welcome to Conversational Mode!
            </h3>
            <p style="color: #2D3748; margin: 0;">
                You're now using our new AI chat interface. Instead of showing search results, 
                I'll have natural conversations with you about Islamic topics, providing 
                personalized guidance based on the Quran, Hadith, and scholarly consensus.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Mark onboarding as shown
    st.session_state.interface_onboarding_shown = True


# --- SECTION 6: HEALTH CHECK ENDPOINT ---
def setup_health_check():
    """Setup health check endpoint for Railway"""
    
    # Railway health check endpoint
    if st.sidebar.button("Health Check"):
        st.sidebar.success("✅ Application is healthy")
        st.sidebar.write("All systems operational")


# --- SECTION 7: ERROR HANDLING & DEBUGGING ---
def handle_app_errors():
    """Global error handler for the application"""
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred. Please refresh the page.")
        
        # Show error details in expander for debugging
        with st.expander("🐛 Error Details (for debugging)"):
            st.exception(e)
        
        # Log error
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


# --- SECTION 8: APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    
    # Check if this is a health check request
    if os.environ.get('HEALTHCHECK'):
        print("Health check passed")
        exit(0)
    
    # Run the application with error handling
    handle_app_errors()


# --- RAILWAY DEPLOYMENT HELPER SCRIPT ---
def railway_deploy_check():
    """
    Helper function to check Railway deployment status
    Run this separately to verify deployment configuration
    """
    
    print("🚄 Railway Deployment Check")
    print("=" * 40)
    
    # Check environment
    print(f"PORT: {os.environ.get('PORT', 'Not set')}")
    print(f"Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not detected')}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Check required files
    required_files = [
        "app.py",
        "requirements.txt",
        ".streamlit/config.toml",
        "static/halalbot_logo.png",
        "static/halalbot_favicon.ico",
        # NEW: Check for conversational components
        "services/conversational_service.py",
        "components/conversational_search_ui.py"
    ]
    
    print("\nFile Check:")
    for file in required_files:
        exists = os.path.exists(file)
        status = "✅" if exists else "❌"
        print(f"{status} {file}")
    
    # Check components
    print("\nComponent Check:")
    try:
        from components.styling import apply_custom_css
        print("✅ Styling component")
    except Exception as e:
        print(f"❌ Styling component: {e}")
    
    try:
        from components.auth_ui import show_login
        print("✅ Auth component")
    except Exception as e:
        print(f"❌ Auth component: {e}")
    
    try:
        from components.search_ui import create_search_interface
        print("✅ Traditional search component")
    except Exception as e:
        print(f"❌ Traditional search component: {e}")
    
    try:
        from components.conversational_search_ui import create_conversational_search_interface
        print("✅ Conversational search component")
    except Exception as e:
        print(f"❌ Conversational search component: {e}")
    
    try:
        from services.conversational_service import search_conversational
        print("✅ Conversational service")
    except Exception as e:
        print(f"❌ Conversational service: {e}")
    
    print("\n" + "=" * 40)
    print("Deployment check complete!")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "check":
    railway_deploy_check()
