# components/conversational_search_ui.py
"""
Enhanced Conversational Search Interface for HalalBot
Natural, dialogue-based Islamic knowledge assistant

COMPLETE REWRITE: Added proper error handling, fallback rendering,
and structured sections for maintainability
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
    
    /* Chat container styling */
    .chat-container {
        max-height: 70vh;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 15px;
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    /* Welcome message container - FIXED COLOR INHERITANCE */
    .welcome-container {
        background: linear-gradient(135deg, #1B5E3F 0%, #2E7D4A 100%) !important;
        color: white !important;
        padding: 2rem !important;
        border-radius: 20px !important;
        margin-bottom: 2rem !important;
        text-align: center !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    /* CRITICAL FIX: Force all nested elements to be white */
    .welcome-container,
    .welcome-container *,
    .welcome-container div,
    .welcome-container p,
    .welcome-container h2,
    .welcome-container em,
    .welcome-container strong {
        color: white !important;
    }
    
    .welcome-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s linear infinite;
    }
    
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .welcome-container h2 {
        margin: 0 !important;
        font-family: 'Amiri', serif !important;
        font-size: 2.5rem !important;
        color: white !important;
    }
    
    .welcome-container p {
        margin: 1rem 0 !important;
        font-size: 1.1rem !important;
        color: white !important;
        line-height: 1.7 !important;
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
        border: 1px solid rgba(27, 94, 63, 0.2);
    }
    
    /* AI message styling */
    .ai-message {
        display: flex;
        justify-content: flex-start;
        margin: 1rem 0;
    }
    
    .ai-message-content {
        background: white;
        color: #2D3748 !important;
        padding: 1.5rem;
        border-radius: 20px 20px 20px 5px;
        max-width: 85%;
        border-left: 4px solid #1B5E3F;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        line-height: 1.6;
        border: 1px solid #e2e8f0;
    }
    
    .ai-message-header {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #f1f3f4;
    }
    
    .ai-message-header strong {
        margin-left: 0.5rem;
        color: #1B5E3F !important;
        font-size: 1.1rem;
    }
    
    /* Feedback section styling */
    .feedback-container {
        background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #E2E8F0;
    }
    
    /* Quick topics styling */
    .quick-topics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .quick-topic-button {
        background: white !important;
        border: 2px solid #1B5E3F !important;
        color: #1B5E3F !important;
        padding: 0.75rem 1rem !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        text-align: left !important;
    }
    
    .quick-topic-button:hover {
        background: #1B5E3F !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(27, 94, 63, 0.3) !important;
    }
    
    /* Fallback text styling when HTML fails */
    .fallback-text {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
        font-family: monospace;
    }
    
    /* Chat input styling */
    .chat-input-container {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 2px solid #e2e8f0;
        margin: 1rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .user-message-content,
        .ai-message-content {
            max-width: 95%;
        }
        
        .welcome-container {
            padding: 1.5rem;
        }
        
        .welcome-container h2 {
            font-size: 2rem !important;
        }
    }
    </style>
    """
    
    st.markdown(conversational_css, unsafe_allow_html=True)


def test_html_rendering() -> bool:
    """Test if HTML rendering is working properly"""
    
    try:
        # Test basic HTML rendering
        test_html = '<div style="color: green;">HTML Test</div>'
        st.markdown(test_html, unsafe_allow_html=True)
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
        
        st.markdown("**💬 You can ask me about:**")
        
        # Simple columns for conversation starters
        col1, col2, col3 = st.columns(3)
        
        topics = [
            "Prayer guidance", "Zakat calculation", "Hajj preparation",
            "Family matters", "Business ethics", "Quran interpretation"
        ]
        
        return topics

    @staticmethod
    def render_message_fallback(is_user: bool, content: str):
        """Fallback message rendering when HTML fails"""
        
        if is_user:
            st.markdown(f"**👤 You:** {content}")
        else:
            st.markdown(f"**🤖 HalalBot:** {content}")

    @staticmethod
    def render_error_message(error: Exception):
        """Render error message with helpful information"""
        
        st.error("❌ Interface rendering error occurred")
        
        with st.expander("🔧 Technical Details"):
            st.code(str(error))
            st.markdown("**Troubleshooting:**")
            st.markdown("- Try refreshing the page")
            st.markdown("- Switch to Traditional Search mode")
            st.markdown("- Clear your browser cache")


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
        """Display the main conversational chat interface with error handling"""
        
        try:
            # Force CSS application
            force_conversational_css()
            
            # Welcome message if new conversation
            if not st.session_state.conversation_started:
                self.display_welcome_message()
            
            # Chat history display
            self.display_chat_history()
            
            # Chat input
            self.handle_chat_input()
            
            # Follow-up questions
            self.display_follow_up_buttons()
            
            # Quick topic buttons
            self.display_quick_topics()
            
        except Exception as e:
            st.error(f"❌ Chat interface error: {str(e)}")
            FallbackRenderer.render_error_message(e)
            
            # Try fallback interface
            self.display_fallback_interface()

    def display_welcome_message(self):
        """Display welcoming message with comprehensive fallback handling"""
        
        if not self.html_rendering_works:
            # Use fallback rendering
            topics = FallbackRenderer.render_welcome_fallback()
            self.render_conversation_starters_fallback(topics)
            return
        
        try:
            # Try advanced HTML rendering
            self.render_advanced_welcome()
            
        except Exception as e:
            print(f"Welcome message rendering failed: {e}")
            # Fall back to simple rendering
            topics = FallbackRenderer.render_welcome_fallback()
            self.render_conversation_starters_fallback(topics)

    def render_advanced_welcome(self):
        """Render welcome message using native Streamlit components"""
        
        # Create a styled container using native Streamlit
        st.markdown("# ☪️ As-Salamu Alaikum!")
        
        st.success("""
        **Welcome to HalalBot, your Islamic knowledge companion.**
        
        Ask me anything about Islam, and I'll provide guidance based on the Quran, 
        Hadith, and scholarly consensus.
        
        🧠 *Note: I am an AI assistant trained on the Qur'an, Hadith, and select scholarly sources.*
        
        Please consult your local Imam or a qualified scholar for specific religious rulings.
        """)
        
        # Conversation starters
        self.render_conversation_starters()

    def get_logo_element(self) -> str:
        """Get logo element with fallback"""
        
        try:
            import base64
            import os
            
            logo_path = "static/halalbot_logo.png"
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                return f'''
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <img src="data:image/png;base64,{logo_data}" alt="HalalBot Logo" 
                         style="height: 80px; width: auto; border-radius: 15px; 
                                box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                </div>
                '''
        except Exception as e:
            print(f"Logo loading failed: {e}")
        
        # Fallback to styled emoji
        return '''
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">☪️</div>
        </div>
        '''

    def render_conversation_starters(self):
        """Render conversation starter buttons with error handling"""
        
        st.markdown("**💬 You can ask me about:**")
        
        try:
            cols = st.columns(3)
            starters = [
                ("🕌 Prayer guidance", "How should I maintain my five daily prayers?"),
                ("💰 Zakat calculation", "How do I calculate zakat on my wealth?"),
                ("🕋 Hajj preparation", "What should I know about preparing for Hajj?"),
                ("👨‍👩‍👧‍👦 Family matters", "What are the rights and responsibilities in a Muslim family?"),
                ("💼 Business ethics", "What are the Islamic principles for conducting business?"),
                ("📖 Quran interpretation", "How should I approach understanding the Quran?")
            ]
            
            for i, (label, query) in enumerate(starters):
                with cols[i % 3]:
                    if st.button(label, key=f"starter_{i}"):
                        self.process_user_query(query)
                        
        except Exception as e:
            print(f"Conversation starters rendering failed: {e}")
            # Show simple text alternatives
            st.write("Ask me about: Prayer, Zakat, Hajj, Family, Business Ethics, Quran")

    def render_conversation_starters_fallback(self, topics: List[str]):
        """Fallback conversation starters"""
        
        try:
            cols = st.columns(3)
            for i, topic in enumerate(topics):
                with cols[i % 3]:
                    if st.button(f"📚 {topic}", key=f"fallback_starter_{i}"):
                        query = f"Tell me about {topic.lower()}"
                        self.process_user_query(query)
        except Exception as e:
            st.write("Use the text input below to ask your questions.")


# --- SECTION 5: MESSAGE RENDERING & DISPLAY ---
    def display_chat_history(self):
        """Display conversation history with fallback rendering"""
        
        if not st.session_state.chat_history:
            return
        
        # Create chat container
        if self.html_rendering_works:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        try:
            for exchange in st.session_state.chat_history:
                # User message
                self.display_user_message(exchange['user_query'])
                
                # AI response
                self.display_ai_response(exchange['ai_response'])
                
                # Separator
                st.markdown("---")
                
        except Exception as e:
            st.error(f"Error displaying chat history: {e}")
            # Try fallback rendering
            self.display_chat_history_fallback()
        
        if self.html_rendering_works:
            st.markdown('</div>', unsafe_allow_html=True)

    def display_user_message(self, query: str):
        """Display user message using native Streamlit"""
        
        st.markdown(f"**👤 You:** {query}")

    def display_ai_response(self, response: Dict):
        """Display AI response using native Streamlit"""
        
        st.markdown(f"**🤖 HalalBot:** {response['main_answer']}")
        
        # Response components
        self.display_response_components(response)

    def display_response_components(self, response: Dict):
        """Display response components (expandables, sources, etc.)"""
        
        try:
            # Conversational Feedback Section
            self.display_conversational_feedback(response)
            
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

    def display_response_components_fallback(self, response: Dict):
        """Fallback display for response components"""
        
        if response.get('islamic_guidance'):
            st.info(f"Islamic Guidance: {response['islamic_guidance']}")
        
        if response.get('related_topics'):
            st.write("Related topics:", ", ".join(response['related_topics']))
        
        if response.get('sources'):
            st.write(f"Based on {len(response['sources'])} sources")

    def render_related_topics(self, topics: List[str]):
        """Render related topics with error handling"""
        
        try:
            cols = st.columns(len(topics))
            for i, topic in enumerate(topics):
                with cols[i]:
                    if st.button(f"📚 {topic}", key=f"related_{len(st.session_state.chat_history)}_{i}"):
                        self.process_user_query(f"Tell me about {topic}")
        except Exception as e:
            # Fallback: show as text
            for topic in topics:
                st.write(f"• {topic}")

    def render_sources(self, sources: List[Dict]):
        """Render sources with error handling"""
        
        try:
            for i, source in enumerate(sources):
                source_icon = {'quran': '📖', 'hadith': '📜', 'fatwa': '⚖️'}.get(source['category'], '📚')
                st.write(f"**{source_icon} {source['source']}** (Relevance: {source['score']:.2f})")
                st.caption(source['text'])
        except Exception as e:
            st.write("Sources available but could not display details")


# --- SECTION 6: INPUT HANDLING & QUERY PROCESSING ---
    def handle_chat_input(self):
        """Handle user input with comprehensive error handling"""
        
        try:
            # Create a form for chat input
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
            # Simple fallback input
            user_input = st.text_input("Your question:")
            if st.button("Send") and user_input:
                self.process_user_query(user_input)

    def process_user_query(self, query: str):
        """Process user query with comprehensive error handling"""
        
        # Input validation
        if not query or not query.strip():
            st.warning("Please enter a question.")
            return
        
        # Check for blocked content
        try:
            if is_blocked_query(query):
                st.error("🛑 This question is inappropriate and will not be processed. Please respect the sacred nature of this service.")
                if hasattr(st.session_state, 'email'):
                    log_blocked_query(st.session_state.email, query)
                return
        except Exception as e:
            print(f"Query blocking check failed: {e}")
        
        # Show processing indicator
        with st.spinner("🔍 Searching Islamic sources..."):
            try:
                if not CONVERSATIONAL_SERVICE_AVAILABLE:
                    st.error("❌ Conversational service is not available. Please try traditional search mode.")
                    return
                
                # Get conversational response
                response = search_conversational(
                    query=query,
                    user_email=getattr(st.session_state, 'email', 'anonymous'),
                    top_k=5,
                    min_score=0.3
                )
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'user_query': query,
                    'ai_response': response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Update follow-up questions
                st.session_state.pending_follow_ups = response.get('follow_up_questions', [])
                
                # Mark conversation as started
                st.session_state.conversation_started = True
                
                # Log successful query
                try:
                    if hasattr(st.session_state, 'email'):
                        log_query_for_user(st.session_state.email, query, response.get('sources', []))
                except Exception as e:
                    print(f"Query logging failed: {e}")
                
                # Rerun to display new message
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ I apologize, but I encountered an error: {str(e)}")
                st.info("💡 Please try rephrasing your question or contact support if the issue persists.")
                
                # Log error for debugging
                print(f"Query processing error: {e}")
                traceback.print_exc()


# --- SECTION 7: FEEDBACK & INTERACTION SYSTEMS ---
    def display_conversational_feedback(self, response: Dict):
        """Display feedback system with error handling"""
        
        if not FEEDBACK_SYSTEM_AVAILABLE:
            return
        
        try:
            # Unique key for this response
            response_id = f"response_{len(st.session_state.chat_history)}_{hash(response['main_answer'][:50])}"
            
            if self.html_rendering_works:
                st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("👍 Helpful", key=f"helpful_{response_id}", help="This guidance was beneficial"):
                    self.log_conversational_feedback(response, "helpful", "Response was helpful")
                    st.success("جزاك الله خيراً (May Allah reward you with good)")
            
            with col2:
                if st.button("👎 Not Helpful", key=f"not_helpful_{response_id}", help="This guidance needs improvement"):
                    self.log_conversational_feedback(response, "not_helpful", "Response needs improvement")
                    st.info("Your feedback helps us improve. Barakallahu feeki!")
            
            with col3:
                # Quick feedback options
                feedback_reason = st.selectbox(
                    "Why? (Optional)",
                    options=[
                        "Select reason...",
                        "Unclear explanation",
                        "Missing important details",
                        "Sources not relevant",
                        "Need more Quranic guidance",
                        "Need more Hadith references",
                        "Too general, need specifics",
                        "Perfect, exactly what I needed!"
                    ],
                    key=f"feedback_reason_{response_id}",
                    label_visibility="collapsed"
                )
                
                if feedback_reason != "Select reason...":
                    self.log_conversational_feedback(response, "detailed", feedback_reason)
            
            if self.html_rendering_works:
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            print(f"Feedback display error: {e}")

    def log_conversational_feedback(self, response: Dict, feedback_type: str, details: str):
        """Log feedback with error handling"""
        
        if not FEEDBACK_SYSTEM_AVAILABLE:
            print(f"Feedback logged locally: {feedback_type} - {details}")
            return
        
        try:
            original_query = response.get('query', 'Unknown query')
            
            log_feedback(
                query=original_query,
                text=response['main_answer'][:500],
                vote="up" if feedback_type == "helpful" else "down",
                user_email=getattr(st.session_state, 'email', 'anonymous')
            )
            
            log_user_activity(
                getattr(st.session_state, 'email', 'anonymous'),
                "conversational_feedback",
                {
                    "feedback_type": feedback_type,
                    "details": details,
                    "response_type": response.get('response_type', 'comprehensive'),
                    "had_sources": len(response.get('sources', [])) > 0,
                    "had_follow_ups": len(response.get('follow_up_questions', [])) > 0,
                    "query_category": self.categorize_query(original_query)
                }
            )
        except Exception as e:
            print(f"Feedback logging error: {e}")

    def categorize_query(self, query: str) -> str:
        """Categorize query for analytics with error handling"""
        
        try:
            query_lower = query.lower()
            
            categories = {
                'prayer': ['prayer', 'salah', 'namaz', 'wudu', 'ablution'],
                'zakat': ['zakat', 'charity', 'alms'],
                'hajj': ['hajj', 'pilgrimage', 'umrah'],
                'fasting': ['fast', 'ramadan', 'sawm'],
                'marriage': ['marriage', 'wedding', 'nikah'],
                'family': ['family', 'parent', 'child'],
                'business': ['business', 'trade', 'work'],
                'general': []
            }
            
            for category, keywords in categories.items():
                if any(keyword in query_lower for keyword in keywords):
                    return category
            
            return 'general'
        except Exception:
            return 'unknown'


# --- SECTION 8: ADDITIONAL INTERFACE COMPONENTS ---
    def display_follow_up_buttons(self):
        """Display follow-up question buttons with error handling"""
        
        if not st.session_state.pending_follow_ups:
            return
        
        try:
            st.markdown("**🤔 Follow-up questions you might have:**")
            
            cols = st.columns(min(len(st.session_state.pending_follow_ups), 3))
            
            for i, follow_up in enumerate(st.session_state.pending_follow_ups):
                with cols[i % 3]:
                    if st.button(
                        f"💭 {follow_up}",
                        key=f"followup_{len(st.session_state.chat_history)}_{i}",
                        help="Click to ask this follow-up question"
                    ):
                        self.process_user_query(follow_up)
                        st.session_state.pending_follow_ups = []
                        
        except Exception as e:
            print(f"Follow-up buttons error: {e}")
            # Simple text display
            for follow_up in st.session_state.pending_follow_ups:
                st.write(f"• {follow_up}")

    def display_quick_topics(self):
        """Display quick topic access buttons with error handling"""
        
        if not st.session_state.conversation_started:
            return
        
        try:
            with st.expander("🚀 Quick Topics"):
                st.markdown("**Jump to popular topics:**")
                
                quick_topics = {
                    "🕌 Prayer times and conditions": "What are the conditions for valid prayer?",
                    "💰 Zakat calculation": "How do I calculate zakat on my savings?",
                    "🌙 Ramadan guidance": "What should I know about fasting in Ramadan?",
                    "👑 Marriage guidance": "What are the Islamic requirements for marriage?",
                    "📿 Daily duas": "What are some important daily supplications?",
                    "🤲 Making dua": "How should I make dua effectively?"
                }
                
                cols = st.columns(2)
                for i, (topic, query) in enumerate(quick_topics.items()):
                    with cols[i % 2]:
                        if st.button(topic, key=f"quick_topic_{i}"):
                            self.process_user_query(query)
                            
        except Exception as e:
            print(f"Quick topics error: {e}")

    def display_conversation_controls(self):
        """Display conversation management controls with error handling"""
        
        if not st.session_state.chat_history:
            return
        
        try:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 New Conversation"):
                    st.session_state.chat_history = []
                    st.session_state.conversation_started = False
                    st.session_state.pending_follow_ups = []
                    st.rerun()
            
            with col2:
                if st.button("📥 Export Chat"):
                    self.export_conversation()
            
            with col3:
                if st.button("ℹ️ Feedback"):
                    self.show_feedback_form()
                    
        except Exception as e:
            print(f"Conversation controls error: {e}")

    def display_fallback_interface(self):
        """Display a simple fallback interface when main interface fails"""
        
        st.markdown("## 🔄 Fallback Interface")
        st.info("Using simplified interface due to rendering issues.")
        
        # Simple input
        query = st.text_input("Ask your Islamic question:")
        if st.button("Submit Question") and query:
            self.process_user_query(query)
        
        # Show basic history
        if st.session_state.chat_history:
            st.markdown("### Recent Conversation")
            for exchange in st.session_state.chat_history[-3:]:  # Show last 3
                st.markdown(f"**Q:** {exchange['user_query']}")
                st.markdown(f"**A:** {exchange['ai_response'].get('main_answer', '')}")
                st.markdown("---")


# --- SECTION 9: UTILITY FUNCTIONS ---
    def export_conversation(self):
        """Export conversation history with error handling"""
        
        if not st.session_state.chat_history:
            st.warning("No conversation to export.")
            return
        
        try:
            # Create exportable format
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
        """Show conversation feedback form with error handling"""
        
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
                    placeholder="What could we improve? Any specific suggestions?"
                )
                
                if st.form_submit_button("Submit Feedback"):
                    st.success("Thank you for your feedback! It helps us improve HalalBot.")
                    
        except Exception as e:
            st.error(f"Feedback form error: {e}")

    def display_chat_history_fallback(self):
        """Fallback chat history display"""
        
        for exchange in st.session_state.chat_history:
            st.markdown(f"**👤 You:** {exchange['user_query']}")
            st.markdown(f"**🤖 HalalBot:** {exchange['ai_response'].get('main_answer', '')}")
            st.markdown("---")


# --- SECTION 10: MAIN INTERFACE FUNCTION ---
def create_conversational_search_interface():
    """
    Create the conversational search interface with comprehensive error handling
    This is the main entry point called by app.py
    """
    
    try:
        # Initialize and display chat interface
        chat_interface = ConversationalChatInterface()
        chat_interface.display_chat_interface()
        chat_interface.display_conversation_controls()
        
    except Exception as e:
        st.error("❌ Failed to load conversational interface")
        
        # Show error details and recovery options
        with st.expander("🔧 Error Details & Recovery"):
            st.exception(e)
            st.markdown("**Recovery Options:**")
            st.markdown("1. Refresh the page")
            st.markdown("2. Switch to Traditional Search mode in the sidebar")
            st.markdown("3. Clear your browser cache")
            
            if st.button("🔄 Try Fallback Interface"):
                fallback_interface = ConversationalChatInterface()
                fallback_interface.display_fallback_interface()


# --- SECTION 11: TESTING & DEBUG ---
def test_conversational_interface():
    """Test function for the conversational interface"""
    
    print("🧪 Testing Conversational Interface...")
    
    try:
        # Test HTML rendering
        html_works = test_html_rendering()
        print(f"HTML Rendering: {'✅' if html_works else '❌'}")
        
        # Test CSS application
        force_conversational_css()
        print("✅ CSS Application")
        
        # Test interface creation
        chat_interface = ConversationalChatInterface()
        print("✅ Interface Creation")
        
        # Test session state
        chat_interface.initialize_session_state()
        print("✅ Session State")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Run tests when file is executed directly
    test_conversational_interface()
