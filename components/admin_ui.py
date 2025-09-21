# components/admin_ui.py
"""
Admin dashboard components for HalalBot application
Handles admin interface and management tools
"""

import streamlit as st
from typing import List, Dict, Any

from core.auth import get_user_count, get_admin_count, update_user_admin_status
from core.invite_codes import (
    get_invite_code_stats, create_invite_code, create_multiple_invite_codes,
    list_unused_invite_codes, list_used_invite_codes, delete_invite_code
)
from core.query_blocking import get_blocked_phrases, add_blocked_phrase, remove_blocked_phrase
from components.auth_ui import require_admin


@require_admin
def show_admin_dashboard():
    """Display the main admin dashboard"""
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    
    with st.expander("🛠️ Admin Dashboard", expanded=True):
        # Overview stats
        show_admin_overview()
        
        st.markdown("---")
        
        # Admin sections
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "👥 Users", "🎫 Invite Codes", "🚫 Blocked Queries", "📊 Analytics"
        ])
        
        with admin_tab1:
            show_user_management()
        
        with admin_tab2:
            show_invite_code_management()
        
        with admin_tab3:
            show_blocked_query_management()
        
        with admin_tab4:
            show_analytics_dashboard()
    
    st.markdown('</div>', unsafe_allow_html=True)


def show_admin_overview():
    """Display admin overview statistics"""
    st.subheader("📈 System Overview")
    
    # Get statistics
    user_count = get_user_count()
    admin_count = get_admin_count()
    invite_stats = get_invite_code_stats()
    
    # Display in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", user_count)
    
    with col2:
        st.metric("Admin Users", admin_count)
    
    with col3:
        st.metric("Total Invite Codes", invite_stats["total"])
    
    with col4:
        st.metric("Used Codes", invite_stats["used"])


def show_user_management():
    """Display user management interface"""
    st.subheader("👥 User Management")
    
    # Load users for management
    from core.auth import load_users
    users = load_users()
    
    if not users:
        st.info("No users found.")
        return
    
    # User list
    st.write("**Current Users:**")
    for email, user_data in users.items():
        is_admin = user_data.get("is_admin", False)
        invite_code = user_data.get("invite_code", "Unknown")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            admin_badge = " 👑" if is_admin else ""
            st.write(f"{email}{admin_badge}")
            st.caption(f"Invite Code: {invite_code}")
        
        with col2:
            # Toggle admin status
            current_status = "Admin" if is_admin else "User"
            st.write(f"Role: {current_status}")
        
        with col3:
            # Admin toggle button
            if st.button(f"Toggle Admin", key=f"toggle_{email}"):
                new_status = not is_admin
                if update_user_admin_status(email, new_status):
                    st.success(f"Updated {email} admin status to {new_status}")
                    st.rerun()
                else:
                    st.error("Failed to update user status")


def show_invite_code_management():
    """Display invite code management interface"""
    st.subheader("🎫 Invite Code Management")
    
    # Stats
    stats = get_invite_code_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", stats["total"])
    with col2:
        st.metric("Used", stats["used"])
    with col3:
        st.metric("Available", stats["unused"])
    
    # Create new codes section
    st.write("**Create New Codes:**")
    
    create_col1, create_col2 = st.columns(2)
    
    with create_col1:
        # Single code creation
        st.write("*Single Code:*")
        custom_code = st.text_input("Custom Code (optional)", key="custom_code")
        code_description = st.text_input("Description", key="code_description")
        
        if st.button("Create Code", key="create_single"):
            code_to_create = custom_code if custom_code else None
            success, result = create_invite_code(code_to_create, code_description)
            
            if success:
                st.success(f"Created invite code: **{result}**")
            else:
                st.error(result)
    
    with create_col2:
        # Multiple code creation
        st.write("*Bulk Creation:*")
        code_count = st.number_input("Number of codes", min_value=1, max_value=50, value=5)
        code_prefix = st.text_input("Prefix (optional)", key="code_prefix")
        
        if st.button("Create Multiple", key="create_multiple"):
            created_codes = create_multiple_invite_codes(code_count, code_prefix)
            
            if created_codes:
                st.success(f"Created {len(created_codes)} invite codes:")
                for code in created_codes:
                    st.code(code)
            else:
                st.error("Failed to create codes")
    
    # List existing codes
    st.write("**Unused Codes:**")
    unused_codes = list_unused_invite_codes()
    
    if unused_codes:
        # Show in columns for better layout
        cols = st.columns(3)
        for i, code in enumerate(unused_codes):
            with cols[i % 3]:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.code(code)
                with col_b:
                    if st.button("❌", key=f"delete_{code}", help="Delete code"):
                        if delete_invite_code(code):
                            st.success(f"Deleted {code}")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
    else:
        st.info("No unused codes available.")
    
    # Show used codes
    with st.expander("📋 Used Codes History"):
        used_codes = list_used_invite_codes()
        
        if used_codes:
            for code_info in used_codes:
                st.write(f"**{code_info['code']}** - {code_info['email']}")
                if code_info['used_at'] != "Unknown":
                    st.caption(f"Used: {code_info['used_at']}")
        else:
            st.info("No codes have been used yet.")


def show_blocked_query_management():
    """Display blocked query management interface"""
    st.subheader("🚫 Blocked Query Management")
    
    # Add new blocked phrase
    st.write("**Add Blocked Phrase:**")
    new_phrase = st.text_input("Phrase to block", key="new_blocked_phrase")
    
    if st.button("Add Phrase", key="add_blocked"):
        if new_phrase:
            if add_blocked_phrase(new_phrase):
                st.success(f"Added blocked phrase: {new_phrase}")
                st.rerun()
            else:
                st.error("Failed to add phrase")
        else:
            st.warning("Please enter a phrase to block")
    
    # List current blocked phrases
    st.write("**Current Blocked Phrases:**")
    blocked_phrases = get_blocked_phrases()
    
    if blocked_phrases:
        for phrase in blocked_phrases:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"• {phrase}")
            
            with col2:
                if st.button("Remove", key=f"remove_{phrase}"):
                    if remove_blocked_phrase(phrase):
                        st.success(f"Removed: {phrase}")
                        st.rerun()
                    else:
                        st.error("Failed to remove phrase")
    else:
        st.info("No blocked phrases configured.")
    
    # Show blocked query log
    with st.expander("📋 Blocked Query Log"):
        try:
            import json
            with open("blocked_queries_log.jsonl", "r") as f:
                blocked_logs = [json.loads(line) for line in f]
            
            if blocked_logs:
                # Show recent blocked queries
                recent_logs = blocked_logs[-10:]  # Last 10
                for log_entry in reversed(recent_logs):
                    st.write(f"**{log_entry.get('timestamp', 'Unknown')}**")
                    st.write(f"User: {log_entry.get('email', 'Unknown')}")
                    st.write(f"Query: {log_entry.get('query', 'Unknown')}")
                    st.markdown("---")
            else:
                st.info("No blocked queries logged yet.")
        except FileNotFoundError:
            st.info("No blocked query log file found.")
        except Exception as e:
            st.error(f"Error reading log: {e}")


def show_analytics_dashboard():
    """Display analytics and statistics"""
    st.subheader("📊 Analytics Dashboard")
    
    # Search analytics
    try:
        import os
        from datetime import datetime, timedelta
        
        st.write("**Search Activity (Last 7 Days):**")
        
        # Count queries from history files
        history_dir = "data/history"
        if os.path.exists(history_dir):
            total_queries = 0
            active_users = set()
            
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for filename in os.listdir(history_dir):
                if filename.endswith('.jsonl'):
                    filepath = os.path.join(history_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            for line in f:
                                try:
                                    import json
                                    entry = json.loads(line)
                                    entry_time = datetime.fromisoformat(entry['timestamp'])
                                    if entry_time >= cutoff_date:
                                        total_queries += 1
                                        # Extract user hash from filename
                                        user_hash = filename.replace('.jsonl', '')
                                        active_users.add(user_hash)
                                except:
                                    continue
                    except:
                        continue
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries (7 days)", total_queries)
            with col2:
                st.metric("Active Users (7 days)", len(active_users))
        
        else:
            st.info("No search history available.")
    
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
    
    # System health
    st.write("**System Health:**")
    
    # Check if required files exist
    required_files = [
        "users.json",
        "invite_codes.json", 
        "blocked_queries.txt"
    ]
    
    file_status = {}
    for file in required_files:
        file_status[file] = "✅" if os.path.exists(file) else "❌"
    
    for file, status in file_status.items():
        st.write(f"{status} {file}")


def show_admin_tools_sidebar():
    """Show admin tools in sidebar if user is admin"""
    from components.auth_ui import is_current_user_admin
    
    if is_current_user_admin():
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Admin Tools")
        
        if st.sidebar.button("📊 View Dashboard"):
            st.session_state.show_admin = True
        
        if st.sidebar.button("🎫 Manage Codes"):
            st.session_state.admin_tab = "codes"
        
        if st.sidebar.button("🚫 Blocked Queries"):
            st.session_state.admin_tab = "blocked"