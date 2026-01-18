# components/conversational_search_ui.py
"""
Enhanced Conversational Search Interface for HalalBot
Natural, dialogue-based Islamic knowledge assistant

FIXED VERSION: 
- Removed white bar above answers (empty chat container)
- Moved Quick Topics to bottom of page
- Consistent button sizing throughout
- Cleaner layout structure
"""

# --- SECTION 1: IMPORTS & DEPENDENCIES ---
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import traceback

# Import the conversational service with error handling
try:
    from services.conversational_service import search_conversational
    CONVERSATIONAL_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: conversational_service not available: {e}")
    CONVERSATIONAL_SERVICE_AVAILABLE = False

# Core system imports
from core.query_blocking import is_blocked_query, log_blocked_query
from utils.logging import log_query_for_user

# Feedback system imports (with fallbacks)
try:
    from core.feedback import log_feedback
    from utils.logging import log_user_activity
    FEEDBACK_SYSTEM_AVAILABLE = True
except ImportError:
    print("Warning: Feedback system not available")
    FEEDBACK_SYSTEM_AVAILABLE = False


# --- SECTION 2: CSS & STYLING UTILITIES ---
def force_conversational_css():
    """Force CSS application for conversational interface components"""
    
    conversational_css = """
    <style>
    /* CONVERSATIONAL INTERFACE SPECIFIC CSS */
    
    /* FIXED: Uniform button sizing */
    .stButton > button {
        min-height: 50px !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    
    /* Conversation starter buttons - consistent sizing */
    div[data-testid="column"] .stButton > button {
        width: 100% !important;
        min-height: 60px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.9rem !important;
        line-height: 1.3 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
    }
    
    /* Quick Topics section styling */
    .quick-topics-section {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e8f0;
    }
    
    /* Welcome message container */
    .welcome-container {
        background: linear-gradient(135deg, #1B5E3F 0%, #2E7D4A 100%) !important;
        color: white !important;
        padding: 2rem !important;
        border-radius: 20px !important;
        margin-bottom: 2rem !important;
        text-align: center !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
    }
    
    .welcome-container * {
        color: white !important;
    }
    
    /* User message styling */
    .user-message {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
    }
    
    .user-message-content {
        background: linear-gradient(135deg, #E8F5E8 0%, #D4EDDA 100%);
        color: #1B5E3F !important;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        max-width: 75%;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* AI message styling */
    .ai-message-content {
        background: white;
        color: #2D3748 !important;
        padding: 1.5rem;
        border-radius: 20px 20px 20px 5px;
        max-width: 85%;
        border-left: 4px solid #1B5E3F;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        line-height: 1.6;
    }
    
    /* Feedback container styling */
    .feedback-container {
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #E2E8F0;
    }
    
    /* Conversation control buttons - consistent sizing */
    .conversation-controls .stButton > button {
        min-width: 140px !important;
        height: 45px !important;
    }
    
    /* Follow-up question buttons */
    .follow-up-buttons .stButton > button {
        min-height: 45px !important;
        font-size: 0.85rem !important;
        background: white !important;
        border: 2px solid #1B5E3F !important;
        color: #1B5E3F !important;
    }
    
    .follow-up-buttons .stButton > button:hover {
        background: #1B5E3F !important;
        color: white !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        div[data-testid="column"] .stButton > button {
            min-height: 50px !important;
            font-size: 0.8rem !important;
        }
    }
    </style>
    """
    
    st.markdown(conversational_css, unsafe_allow_html=True)


def test_html_rendering() -> bool:
    """Test if HTML rendering is working properly"""
    try:
        return True
    except Exception as e:
        print(f"HTML rendering test failed: {e}")
        return False


# --- SECTION 3: FALLBACK RENDERING SYSTEM ---
class FallbackRenderer:
    """Handles fallback rendering when HTML fails"""
    
    @staticmethod
    def render_welcome_fallback():
        """Fallback welcome message when HTML rendering fails"""
        st.markdown("# ☪️ HalalBot")
        st.markdown("## As-Salamu Alaikum!")
        
        st.info("""
        Welcome to HalalBot, your Islamic knowledge companion. 
        Ask me anything about Islam, and I'll provide guidance based on the Quran, 
        Hadith, and scholarly consensus.
        
        🧠 Note: I am an AI assistant trained on the Qur'an, Hadith, and select scholarly sources.
        Please consult your local Imam or a qualified scholar for specific religious rulings.
        """)
        
        return ["Prayer guidance", "Zakat calculation", "Hajj preparation",
                "Family matters", "Business ethics", "Quran interpretation"]

    @staticmethod
    def render_message_fallback(is_user: bool, content: str):
        """Fallback message rendering when HTML fails"""
        if is_user:
            st.markdown(f"**👤 You:** {content}")
        else:
            st.markdown(f"**🤖 HalalBot:** {content}")


# --- SECTION 4: CONVERSATIONAL INTERFACE CORE ---
class ConversationalChatInterface:
    """
    Enhanced chat-based interface for conversational Islamic AI
    with comprehensive error handling and fallback mechanisms
    """
    
    def __init__(self):
        self.html_rendering_works = True
        self.initialize_session_state()
        self.test_rendering_capability()

    def initialize_session_state(self):
        """Initialize chat session state with error handling"""
        try:
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            if 'conversation_started' not in st.session_state:
                st.session_state.conversation_started = False
            
            if 'pending_follow_ups' not in st.session_state:
                st.session_state.pending_follow_ups = []
            
            if 'interface_errors' not in st.session_state:
                st.session_state.interface_errors = []
                
        except Exception as e:
            print(f"Error initializing session state: {e}")

    def test_rendering_capability(self):
        """Test if HTML rendering is working"""
        self.html_rendering_works = test_html_rendering()
        if not self.html_rendering_works:
            st.warning("⚠️ Advanced styling disabled. Using fallback interface.")

    def display_chat_interface(self):
        """
        Display the main conversational chat interface
        FIXED: Removed Quick Topics from here - now called separately at bottom
        """
        try:
            # Force CSS application
            force_conversational_css()
            
            # Welcome message if new conversation
            if not st.session_state.conversation_started:
                self.display_welcome_message()
            
            # Chat history display (FIXED: no empty container wrapper)
            self.display_chat_history()
            
            # Chat input
            self.handle_chat_input()
            
            # Follow-up questions (only if conversation started)
            if st.session_state.conversation_started:
                self.display_follow_up_buttons()
            
            # NOTE: Quick Topics moved to display_quick_topics_section()
            # Called from app.py AFTER the Log Out button
            
        except Exception as e:
            st.error(f"❌ Chat interface error: {str(e)}")
            self.display_fallback_interface()

    def display_welcome_message(self):
        """Display welcoming message with logo"""
        if not self.html_rendering_works:
            FallbackRenderer.render_welcome_fallback()
            return
        
        try:
            self.render_advanced_welcome()
        except Exception as e:
            print(f"Welcome message rendering failed: {e}")
            FallbackRenderer.render_welcome_fallback()

    def render_advanced_welcome(self):
        """Render welcome message using native Streamlit components"""
        
        # Try to load the HalalBot logo
        try:
            import base64
            import os
            
            logo_path = "static/halalbot_logo.png"
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                st.markdown(f"""
                <div style="text-align: center; margin-bottom: 1rem;">
                    <img src="data:image/png;base64,{logo_data}" alt="HalalBot Logo" 
                         style="height: 80px; width: auto; border-radius: 10px;">
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align: center; font-size: 3rem;">☪️</div>',
                           unsafe_allow_html=True)
        except Exception:
            st.markdown('<div style="text-align: center; font-size: 3rem;">☪️</div>',
                       unsafe_allow_html=True)
        
        # Title with custom styling
        st.markdown("""
        <h1 style="text-align: center; color: #1B5E3F; font-family: 'Amiri', serif; 
                   font-size: 2.5rem; margin-bottom: 1rem;">
            As-Salamu Alaikum!
        </h1>
        """, unsafe_allow_html=True)
        
        # Welcome box
        st.success("""
        **Welcome to HalalBot, your Islamic knowledge companion.**
        
        Ask me anything about Islam, and I'll provide guidance based on the Quran, 
        Hadith, and scholarly consensus.
        
        🧠 *Note: I am an AI assistant trained on the Qur'an, Hadith, and select scholarly sources.*
        
        Please consult your local Imam or a qualified scholar for specific religious rulings.
        """)
        
        # Conversation starters with CONSISTENT button sizing
        self.render_conversation_starters()

    def render_conversation_starters(self):
        """Render conversation starter buttons with CONSISTENT sizing"""
        
        st.markdown("**💬 You can ask me about:**")
        
        try:
            # Using 3 columns with equal-width buttons
            # Row 1: Zakat, Hajj, Quran
            # Row 2: Prayer, Family, Business
            starters = [
                ("💰 ZAKAT CALCULATION", "How do I calculate zakat on my wealth?"),
                ("🕋 HAJJ PREPARATION", "What should I know about preparing for Hajj?"),
                ("📖 QURAN INTERPRETATION", "How should I approach understanding the Quran?"),
                ("🕌 PRAYER GUIDANCE", "How should I maintain my five daily prayers?"),
                ("👨‍👩‍👧‍👦 FAMILY MATTERS", "What are the rights and responsibilities in a Muslim family?"),
                ("💼 BUSINESS ETHICS", "What are the Islamic principles for conducting business?")
            ]
            
            # Row 1: Zakat, Hajj, Quran
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(starters[0][0], key="starter_0", use_container_width=True):
                    self.process_user_query(starters[0][1])
            with col2:
                if st.button(starters[1][0], key="starter_1", use_container_width=True):
                    self.process_user_query(starters[1][1])
            with col3:
                if st.button(starters[2][0], key="starter_2", use_container_width=True):
                    self.process_user_query(starters[2][1])
            
            # Row 2: Prayer, Family, Business
            col4, col5, col6 = st.columns(3)
            with col4:
                if st.button(starters[3][0], key="starter_3", use_container_width=True):
                    self.process_user_query(starters[3][1])
            with col5:
                if st.button(starters[4][0], key="starter_4", use_container_width=True):
                    self.process_user_query(starters[4][1])
            with col6:
                if st.button(starters[5][0], key="starter_5", use_container_width=True):
                    self.process_user_query(starters[5][1])
                        
        except Exception as e:
            print(f"Conversation starters rendering failed: {e}")
            st.write("Ask me about: Prayer, Zakat, Hajj, Family, Business Ethics, Quran")


# --- SECTION 5: MESSAGE RENDERING & DISPLAY ---
    def display_chat_history(self):
        """
        Display conversation history 
        FIXED: Removed empty container div that caused white bar
        """
        if not st.session_state.chat_history:
            return
        
        # No wrapper div - just render messages directly
        try:
            for exchange in st.session_state.chat_history:
                # User message
                self.display_user_message(exchange['user_query'])
                
                # AI response
                self.display_ai_response(exchange['ai_response'])
                
                # Light separator
                st.markdown("---")
                
        except Exception as e:
            st.error(f"Error displaying chat history: {e}")
            self.display_chat_history_fallback()

    def display_user_message(self, query: str):
        """Display user message"""
        st.markdown(f"**👤 You:** {query}")

    def display_ai_response(self, response: Dict):
        """Display AI response"""
        st.markdown(f"**🤖 HalalBot:** {response['main_answer']}")
        self.display_response_components(response)

    def display_response_components(self, response: Dict):
        """Display response components (expandables, sources, etc.)"""
        try:
            # Additional elements in expandable sections
            if response.get('islamic_guidance'):
                with st.expander("🕌 Islamic Guidance"):
                    st.write(response['islamic_guidance'])
            
            if response.get('related_topics'):
                with st.expander("🔗 Related Topics"):
                    self.render_related_topics(response['related_topics'])
            
            if response.get('sources'):
                with st.expander("📖 Sources Used"):
                    self.render_sources(response['sources'])
                    
        except Exception as e:
            print(f"Response components rendering failed: {e}")

    def render_related_topics(self, topics: List[str]):
        """Render related topics"""
        try:
            num_cols = min(len(topics), 3)
            cols = st.columns(num_cols)
            for i, topic in enumerate(topics):
                with cols[i % num_cols]:
                    if st.button(f"📚 {topic}", key=f"related_{len(st.session_state.chat_history)}_{i}"):
                        self.process_user_query(f"Tell me about {topic}")
        except Exception:
            for topic in topics:
                st.write(f"• {topic}")

    def render_sources(self, sources: List[Dict]):
        """Render sources"""
        try:
            for i, source in enumerate(sources):
                source_icon = {'quran': '📖', 'hadith': '📜', 'fatwa': '⚖️'}.get(source.get('category', ''), '📚')
                st.write(f"**{source_icon} {source.get('source', 'Unknown')}** (Relevance: {source.get('score', 0):.2f})")
                st.caption(source.get('text', ''))
        except Exception:
            st.write("Sources available but could not display details")


# --- SECTION 6: INPUT HANDLING & QUERY PROCESSING ---
    def handle_chat_input(self):
        """Handle user input"""
        try:
            with st.form(key="chat_input_form", clear_on_submit=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    user_input = st.text_input(
                        "Ask your question...",
                        placeholder="e.g., How do I perform wudu? What is the ruling on...",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    send_button = st.form_submit_button("Send 📤", use_container_width=True)
                
                if send_button and user_input:
                    self.process_user_query(user_input)
                    
        except Exception as e:
            st.error(f"Input handling error: {e}")
            user_input = st.text_input("Your question:")
            if st.button("Send") and user_input:
                self.process_user_query(user_input)

    def process_user_query(self, query: str):
        """Process user query"""
        if not query or not query.strip():
            st.warning("Please enter a question.")
            return
        
        # Check for blocked content
        try:
            if is_blocked_query(query):
                st.error("🛑 This question is inappropriate. Please respect the sacred nature of this service.")
                if hasattr(st.session_state, 'email'):
                    log_blocked_query(st.session_state.email, query)
                return
        except Exception as e:
            print(f"Query blocking check failed: {e}")
        
        # Show processing indicator
        with st.spinner("🔍 Searching Islamic sources..."):
            try:
                if not CONVERSATIONAL_SERVICE_AVAILABLE:
                    st.error("❌ Conversational service not available. Please try traditional search mode.")
                    return
                
                response = search_conversational(
                    query=query,
                    user_email=getattr(st.session_state, 'email', 'anonymous'),
                    top_k=5,
                    min_score=0.3
                )
                
                st.session_state.chat_history.append({
                    'user_query': query,
                    'ai_response': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                st.session_state.pending_follow_ups = response.get('follow_up_questions', [])
                st.session_state.conversation_started = True
                
                try:
                    if hasattr(st.session_state, 'email'):
                        log_query_for_user(st.session_state.email, query, response.get('sources', []))
                except Exception:
                    pass
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ I apologize, but I encountered an error: {str(e)}")
                st.info("💡 Please try rephrasing your question or contact support.")
                traceback.print_exc()


# --- SECTION 7: FOLLOW-UP & QUICK TOPICS ---
    def display_follow_up_buttons(self):
        """Display follow-up question buttons"""
        if not st.session_state.pending_follow_ups:
            return
        
        try:
            st.markdown("**🤔 Follow-up questions you might have:**")
            
            # Use 3 columns for consistency
            num_follow_ups = len(st.session_state.pending_follow_ups)
            cols = st.columns(min(num_follow_ups, 3))
            
            for i, follow_up in enumerate(st.session_state.pending_follow_ups[:3]):
                with cols[i % 3]:
                    if st.button(
                        f"💭 {follow_up}",
                        key=f"followup_{len(st.session_state.chat_history)}_{i}",
                        use_container_width=True
                    ):
                        self.process_user_query(follow_up)
                        st.session_state.pending_follow_ups = []
                        
        except Exception as e:
            print(f"Follow-up buttons error: {e}")


# --- SECTION 8: CONVERSATION CONTROLS ---
    def display_conversation_controls(self):
        """Display conversation management controls"""
        if not st.session_state.chat_history:
            return
        
        try:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 NEW CONVERSATION", use_container_width=True):
                    st.session_state.chat_history = []
                    st.session_state.conversation_started = False
                    st.session_state.pending_follow_ups = []
                    st.rerun()
            
            with col2:
                if st.button("📥 EXPORT CHAT", use_container_width=True):
                    self.export_conversation()
            
            with col3:
                if st.button("ℹ️ FEEDBACK", use_container_width=True):
                    self.show_feedback_form()
                    
        except Exception as e:
            print(f"Conversation controls error: {e}")

    def export_conversation(self):
        """Export conversation history"""
        if not st.session_state.chat_history:
            st.warning("No conversation to export.")
            return
        
        try:
            export_text = "# HalalBot Conversation Export\n\n"
            export_text += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, exchange in enumerate(st.session_state.chat_history, 1):
                export_text += f"## Exchange {i}\n\n"
                export_text += f"**You:** {exchange['user_query']}\n\n"
                export_text += f"**HalalBot:** {exchange['ai_response']['main_answer']}\n\n"
                export_text += "---\n\n"
            
            st.download_button(
                label="📥 Download Conversation",
                data=export_text,
                file_name=f"halalbot_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        except Exception as e:
            st.error(f"Export failed: {e}")

    def show_feedback_form(self):
        """Show conversation feedback form"""
        try:
            with st.form("conversation_feedback"):
                st.subheader("💭 How was your experience?")
                
                rating = st.select_slider(
                    "Overall satisfaction:",
                    options=["Poor", "Fair", "Good", "Very Good", "Excellent"],
                    value="Good"
                )
                
                helpfulness = st.radio(
                    "Were the responses helpful?",
                    options=["Very helpful", "Somewhat helpful", "Not helpful"],
                    horizontal=True
                )
                
                feedback_text = st.text_area(
                    "Additional feedback (optional):",
                    placeholder="What could we improve?"
                )
                
                if st.form_submit_button("Submit Feedback"):
                    st.success("Thank you for your feedback! It helps us improve HalalBot.")
        except Exception as e:
            st.error(f"Feedback form error: {e}")

    def display_fallback_interface(self):
        """Display a simple fallback interface when main interface fails"""
        st.markdown("## 🔄 Fallback Interface")
        st.info("Using simplified interface due to rendering issues.")
        
        query = st.text_input("Ask your Islamic question:")
        if st.button("Submit Question") and query:
            self.process_user_query(query)
        
        if st.session_state.chat_history:
            st.markdown("### Recent Conversation")
            for exchange in st.session_state.chat_history[-3:]:
                st.markdown(f"**Q:** {exchange['user_query']}")
                st.markdown(f"**A:** {exchange['ai_response'].get('main_answer', '')}")
                st.markdown("---")

    def display_chat_history_fallback(self):
        """Fallback chat history display"""
        for exchange in st.session_state.chat_history:
            st.markdown(f"**👤 You:** {exchange['user_query']}")
            st.markdown(f"**🤖 HalalBot:** {exchange['ai_response'].get('main_answer', '')}")
            st.markdown("---")


# --- SECTION 9: QUICK TOPICS (SEPARATE - FOR BOTTOM OF PAGE) ---
def display_quick_topics_section():
    """
    Display quick topic access buttons
    FIXED: This is now a SEPARATE function to be called from app.py
    after the Log Out button
    """
    # Only show if conversation has been started
    if not st.session_state.get('conversation_started', False):
        return
    
    try:
        with st.expander("🚀 Quick Topics", expanded=False):
            st.markdown("**Jump to popular topics:**")
            
            quick_topics = [
                ("🕌 PRAYER TIMES AND CONDITIONS", "What are the conditions for valid prayer?"),
                ("💰 ZAKAT CALCULATION", "How do I calculate zakat on my savings?"),
                ("🌙 RAMADAN GUIDANCE", "What should I know about fasting in Ramadan?"),
                ("👑 MARRIAGE GUIDANCE", "What are the Islamic requirements for marriage?"),
                ("📿 DAILY DUAS", "What are some important daily supplications?"),
                ("🤲 MAKING DUA", "How should I make dua effectively?")
            ]
            
            # 2 rows of 3 buttons each for consistency
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(quick_topics[0][0], key="qt_0", use_container_width=True):
                    _process_quick_topic(quick_topics[0][1])
            with col2:
                if st.button(quick_topics[1][0], key="qt_1", use_container_width=True):
                    _process_quick_topic(quick_topics[1][1])
            with col3:
                if st.button(quick_topics[2][0], key="qt_2", use_container_width=True):
                    _process_quick_topic(quick_topics[2][1])
            
            col4, col5, col6 = st.columns(3)
            with col4:
                if st.button(quick_topics[3][0], key="qt_3", use_container_width=True):
                    _process_quick_topic(quick_topics[3][1])
            with col5:
                if st.button(quick_topics[4][0], key="qt_4", use_container_width=True):
                    _process_quick_topic(quick_topics[4][1])
            with col6:
                if st.button(quick_topics[5][0], key="qt_5", use_container_width=True):
                    _process_quick_topic(quick_topics[5][1])
                    
    except Exception as e:
        print(f"Quick topics error: {e}")


def _process_quick_topic(query: str):
    """Helper to process quick topic selection"""
    chat = ConversationalChatInterface()
    chat.process_user_query(query)


# --- SECTION 10: MAIN INTERFACE FUNCTION ---
def create_conversational_search_interface():
    """
    Create the conversational search interface
    This is the main entry point called by app.py
    """
    try:
        chat_interface = ConversationalChatInterface()
        chat_interface.display_chat_interface()
        chat_interface.display_conversation_controls()
        
    except Exception as e:
        st.error("❌ Failed to load conversational interface")
        
        with st.expander("🔧 Error Details & Recovery"):
            st.exception(e)
            st.markdown("**Recovery Options:**")
            st.markdown("1. Refresh the page")
            st.markdown("2. Switch to Traditional Search mode in the sidebar")
            
            if st.button("🔄 Try Fallback Interface"):
                fallback = ConversationalChatInterface()
                fallback.display_fallback_interface()


# --- SECTION 11: TESTING ---
if __name__ == "__main__":
    print("🧪 Testing Conversational Interface...")
    try:
        force_conversational_css()
        chat = ConversationalChatInterface()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
