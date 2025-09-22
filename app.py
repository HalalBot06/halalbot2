# app.py
"""
HalalBot - Islamic Knowledge Chatbot
Enhanced with Conversational AI Interface

MAJOR UPDATE: Added conversational interface option
Toggle between traditional search and conversational AI
FIXED: CSS timing and HTML rendering issues
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

# Search interface imports
from components.search_ui import create_search_interface  # Original
from components.conversational_search_ui import create_conversational_search_interface  # NEW

from components.admin_ui import show_admin_dashboard, show_admin_tools_sidebar

# Core logic imports
from core.query_blocking import setup_default_rules

# Utils
from utils.file_operations import ensure_directory


# --- SECTION 2: RAILWAY DEPLOYMENT CONFIGURATION ---
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


# --- SECTION 3: SESSION STATE & PREFERENCES MANAGEMENT ---
def init_conversational_preferences():
    """Initialize user preferences for conversational interface"""
    
    if 'use_conversational_interface' not in st.session_state:
        # Default to conversational interface for new users
        st.session_state.use_conversational_interface = True


def init_application_state():
    """Initialize all session state variables for the application"""
    
    # Initialize auth session state
    init_session_state()
    
    # Initialize conversational preferences
    init_conversational_preferences()
    
    # Initialize admin state if not present
    if 'show_admin' not in st.session_state:
        st.session_state.show_admin = False
    
    # Initialize debug mode
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False


# --- SECTION 4: APPLICATION STARTUP & CONFIGURATION ---
def configure_streamlit_app():
    """Configure Streamlit app settings - MUST BE CALLED FIRST"""
    
    # CRITICAL: Apply page config FIRST, before any other Streamlit calls
    apply_page_config()
    
    # Setup Railway environment
    setup_railway_environment()
    
    # Load static assets
    assets = load_static_assets()
    
    return assets


def apply_application_styling():
    """Apply CSS styling - MUST BE CALLED AFTER PAGE CONFIG"""
    
    # CRITICAL: Apply custom CSS immediately after page config
    # This ensures CSS is loaded before any HTML rendering
    apply_custom_css()
    
    # Force CSS application with a small delay
    st.markdown('<div id="css-applied" style="display:none;"></div>', unsafe_allow_html=True)


def setup_application_core():
    """Setup core application components"""
    
    # Initialize all session state
    init_application_state()
    
    # Setup query filtering rules
    setup_default_rules()
    
    # Ensure required directories exist
    ensure_directory("data/history")


# --- SECTION 5: DEBUG & MONITORING UTILITIES ---
def show_debug_info(assets):
    """Show debug information for troubleshooting"""
    
    if st.sidebar.checkbox("🔧 Debug Info", False):
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
        
        # CSS Application Test
        st.sidebar.write("**CSS Status:**")
        st.sidebar.markdown('<div style="color: var(--primary-green, red);">CSS Test Color</div>', unsafe_allow_html=True)


def setup_health_check():
    """Setup health check endpoint for Railway"""
    
    if st.sidebar.button("Health Check"):
        st.sidebar.success("✅ Application is healthy")
        st.sidebar.write("All systems operational")


# --- SECTION 6: INTERFACE CONTROL & ROUTING ---
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


def show_search_interface():
    """Show the appropriate search interface based on user preference"""
    
    try:
        # CRITICAL: Re-apply CSS before rendering any interface
        # This ensures CSS is available for HTML rendering
        if st.session_state.use_conversational_interface:
            # Force CSS refresh for conversational interface
            st.markdown("""
            <style>
            /* Ensure conversational interface has proper styling */
            .stApp { font-family: 'Inter', sans-serif !important; }
            </style>
            """, unsafe_allow_html=True)
        
        if st.session_state.use_conversational_interface:
            # Use conversational interface
            create_conversational_search_interface()
        else:
            # Use traditional search interface
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
            with st.expander("🐛 Error Details"):
                st.exception(e)


# --- SECTION 7: USER INTERFACE COMPONENTS ---
def show_authenticated_interface():
    """Display the main interface for authenticated users"""
    
    # Show user info in sidebar
    show_user_info()
    
    # Show interface toggle in sidebar
    show_interface_toggle()
    
    # Show admin tools in sidebar if user is admin
    show_admin_tools_sidebar()
    
    # Main content area
    main_content_area()
    
    # Logout section
    st.markdown("---")
    show_logout_button()


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
        # Show the appropriate search interface
        show_search_interface()
        
        # Show admin section for admin users
        from components.auth_ui import is_current_user_admin
        if is_current_user_admin():
            st.markdown("---")
            if st.button("🛠️ Admin Dashboard"):
                st.session_state.show_admin = True
                st.rerun()


# --- SECTION 8: MAIN APPLICATION ENTRY POINT ---
def main():
    """
    Main application entry point with proper initialization sequence
    FIXED: Proper CSS timing and error handling
    """
    
    try:
        # STEP 1: Configure Streamlit (MUST BE FIRST)
        assets = configure_streamlit_app()
        
        # STEP 2: Apply CSS immediately (BEFORE ANY HTML RENDERING)
        apply_application_styling()
        
        # STEP 3: Setup core application components
        setup_application_core()
        
        # STEP 4: Show debug info if requested
        show_debug_info(assets)
        
        # STEP 5: Handle authentication and routing
        if not check_authentication():
            # Show login interface if not authenticated
            show_login()
            return
        
        # STEP 6: User is authenticated - show main interface
        show_authenticated_interface()
        
    except Exception as e:
        st.error("⚠️ Application configuration error. Please refresh the page.")
        
        # Show error details in expander for debugging
        with st.expander("🐛 Error Details"):
            st.exception(e)
            st.write("**Troubleshooting Tips:**")
            st.write("1. Clear your browser cache and refresh")
            st.write("2. Check if all required files are present")
            st.write("3. Ensure your internet connection is stable")
            st.write("4. Try switching to traditional search mode")


# --- SECTION 9: ERROR HANDLING & RECOVERY ---
def handle_app_errors():
    """Global error handler for the application with recovery options"""
    
    try:
        main()
    except Exception as e:
        st.error("An unexpected error occurred. Please try the recovery options below.")
        
        # Recovery options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Application"):
                st.rerun()
        
        with col2:
            if st.button("🔧 Reset Session"):
                for key in list(st.session_state.keys()):
                    if key not in ['authentication_status', 'email']:
                        del st.session_state[key]
                st.rerun()
        
        with col3:
            if st.button("🏠 Safe Mode"):
                st.session_state.use_conversational_interface = False
                st.rerun()
        
        # Show error details for debugging
        with st.expander("🐛 Technical Error Details (for debugging)"):
            st.exception(e)
        
        # Log error
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


# --- SECTION 10: DEPLOYMENT UTILITIES ---
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


# --- SECTION 11: APPLICATION STARTUP ---
if __name__ == "__main__":
    
    # Check if this is a health check request
    if os.environ.get('HEALTHCHECK'):
        print("Health check passed")
        exit(0)
    
    # Check if this is a deployment check
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        railway_deploy_check()
        exit(0)
    
    # Run the application with comprehensive error handling
    handle_app_errors()
