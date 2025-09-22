# components/search_ui.py
"""
Enhanced search interface for HalalBot with modern, beautiful UI
"""

import streamlit as st
from components.styling import (
    create_app_header, create_disclaimer_section, create_search_container,
    create_styled_result_card, create_query_header, create_no_results_message,
    create_search_tips
)
from services.search_service import search_faiss
from core.feedback_utils import log_feedback
from core.query_blocking import is_blocked_query, log_blocked_query
from utils.hashing import hash_text
from utils.logging import log_query_for_user


def create_search_interface():
    """Create the main search interface with enhanced styling"""
    
    # App header with logo and branding
    st.markdown(create_app_header(), unsafe_allow_html=True)
    
    # Disclaimer section
    st.markdown(create_disclaimer_section(), unsafe_allow_html=True)
    
    # Search container
    st.markdown(create_search_container(), unsafe_allow_html=True)
    
    # Search input with custom styling
    st.markdown('<label class="search-label">Ask a question:</label>', unsafe_allow_html=True)
    query = st.text_input(
        "Ask a question:",
        placeholder="e.g., How to perform wudu? What is zakat? Prayer times...",
        label_visibility="collapsed",
        key="main_search"
    )
    # Add this right after the text input
    search_button = st.button("🔍 Search", type="primary")
    
    # Controls section in a grid layout
    st.markdown('<div class="controls-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Number of Responses</div>', unsafe_allow_html=True)
        top_k = st.slider(
            "Number of responses",
            min_value=1,
            max_value=10,
            value=5,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="control-group">', unsafe_allow_html=True)
        st.markdown('<div class="control-label">Minimum Score</div>', unsafe_allow_html=True)
        min_score = st.slider(
            "Minimum score",
            min_value=0.0,
            max_value=1.0,
            value=0.05,
            step=0.01,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close controls-container
    
    # Source filter
    st.markdown('<div class="control-label">Source Filter</div>', unsafe_allow_html=True)
    filter_choice = st.selectbox(
        "Source filter",
        options=[
            "All Sources",
            "Quran only",
            "Hadith only",
            "Fatwa only",
            "Zakat only",
            "Other only"
        ],
        label_visibility="collapsed"
    )
    
    # Search tips in an expander
    st.markdown('<div class="tips-section">', unsafe_allow_html=True)
    with st.expander("💡 Search Tips & Popular Topics"):
        st.markdown(create_search_tips(), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close search-container
    
    # Process search query
    if query and search_button:
        process_search_query(query, top_k, min_score, filter_choice)


def process_search_query(query: str, top_k: int, min_score: float, filter_choice: str):
    """Process the search query and display results"""
    
    # Check for blocked queries
    if is_blocked_query(query):
        st.error("⛔ This question is inappropriate and will not be processed. Please respect the sacred nature of this service.")
        log_blocked_query(st.session_state.email, query)
        return
    
    # Map filter choices
    filter_map = {
        "Quran only": "quran-only",
        "Hadith only": "hadith-only",
        "Fatwa only": "fatwa-only",
        "Zakat only": "zakat-only",
        "Other only": "other-only",
        "All Sources": None
    }
    
    # Display query header
    st.markdown(create_query_header(query), unsafe_allow_html=True)
    
    # Perform search
    try:
        with st.spinner("🔍 Searching through Islamic sources..."):
            results = search_faiss(
                query,
                top_k=top_k,
                min_score=min_score,
                source_filter=filter_map[filter_choice]
            )
        
        if results:
            # Log successful query
            log_query_for_user(st.session_state.email, query, results)
            
            # Display results
            display_search_results(query, results)
        else:
            # No results found
            st.markdown(create_no_results_message(), unsafe_allow_html=True)
            
            # Suggestions for better results
            show_search_suggestions()
            
    except Exception as e:
        st.error(f"❌ Search failed: {str(e)}")
        st.info("💡 Please try again or contact support if the issue persists.")


def display_search_results(query: str, results: list):
    """Display search results with enhanced styling"""
    
    st.markdown('<div class="results-container">', unsafe_allow_html=True)
    
    # Results summary
    st.success(f"✅ Found {len(results)} relevant result(s)")
    
    for i, result in enumerate(results, 1):
        # Display result card
        st.markdown(create_styled_result_card(result, i), unsafe_allow_html=True)
        
        # Feedback section for each result
        create_feedback_section(query, result, i)
    
    st.markdown('</div>', unsafe_allow_html=True)


def create_feedback_section(query: str, result: dict, index: int):
    """Create feedback section for each result"""
    
    result_id = hash_text(result["text"])
    
    with st.expander(f"💭 Was result #{index} helpful?"):
        st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("👍 Yes", key=f"yes_{index}_{result_id}"):
                log_feedback(query, result["text"], "up", st.session_state.email)
                st.success("Thank you for your feedback!")
                
        with col2:
            if st.button("👎 No", key=f"no_{index}_{result_id}"):
                log_feedback(query, result["text"], "down", st.session_state.email)
                st.warning("We'll use your feedback to improve.")
        
        with col3:
            st.info("Your feedback helps improve our responses!")
        
        st.markdown('</div>', unsafe_allow_html=True)


def show_search_suggestions():
    """Show suggestions when no results are found"""
    
    st.markdown("### 💡 Try these suggestions:")
    
    suggestions = [
        "**Lower the minimum score** to see more results",
        "**Use simpler terms**: 'prayer' instead of 'salah timing'",
        "**Try Arabic terms**: 'wudu', 'zakat', 'hajj'",
        "**Ask complete questions**: 'How to perform ablution?'",
        "**Check spelling** of your search terms"
    ]
    
    for suggestion in suggestions:
        st.markdown(f"• {suggestion}")
    
    # Popular search examples
    with st.expander("🔥 Popular Search Examples"):
        examples = [
            "How to perform wudu?",
            "What is the ruling on music in Islam?",
            "Zakat calculation",
            "Prayer times requirements",
            "Halal food guidelines",
            "Marriage in Islam",
            "Business ethics in Islam"
        ]
        
        st.markdown("**Click any example to search:**")
        
        cols = st.columns(2)
        for i, example in enumerate(examples):
            with cols[i % 2]:
                if st.button(f"🔍 {example}", key=f"example_{i}"):
                    st.session_state.main_search = example
                    st.rerun()


def create_quick_search_buttons():
    """Create quick search buttons for common topics"""
    
    st.markdown("### 🚀 Quick Search")
    
    quick_searches = {
        "🕌 Prayer": "prayer requirements",
        "💰 Zakat": "zakat calculation",
        "🕋 Hajj": "hajj pilgrimage",
        "🍽️ Halal": "halal food",
        "💒 Marriage": "marriage islam",
        "📚 Quran": "quran verses"
    }
    
    cols = st.columns(3)
    for i, (label, query) in enumerate(quick_searches.items()):
        with cols[i % 3]:
            if st.button(label, key=f"quick_{i}"):
                st.session_state.main_search = query
                st.rerun()


# Helper function for search metrics
def show_search_metrics():
    """Show search statistics in sidebar (if admin)"""
    
    if st.session_state.get("is_admin", False):
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Search Metrics")
        
        # This would connect to your analytics
        st.sidebar.metric("Total Searches Today", "156")
        st.sidebar.metric("Average Response Time", "0.8s")
        st.sidebar.metric("User Satisfaction", "94%")
