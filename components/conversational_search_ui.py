# components/conversational_search_ui.py
"""
Enhanced conversational search interface for HalalBot
Natural, dialogue-based Islamic knowledge assistant
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime

# Import the conversational service
from services.conversational_service import search_conversational
from core.query_blocking import is_blocked_query, log_blocked_query
from utils.logging import log_query_for_user

class ConversationalChatInterface:
    """
    Chat-based interface for conversational Islamic AI
    """
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize chat session state"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'conversation_started' not in st.session_state:
            st.session_state.conversation_started = False
        
        if 'pending_follow_ups' not in st.session_state:
            st.session_state.pending_follow_ups = []

    def display_chat_interface(self):
        """Display the main conversational chat interface"""
        
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

    def display_welcome_message(self):
        """Display welcoming message for new users"""
        
        # Try to load the actual HalalBot logo
        logo_path = "static/halalbot_logo.png"
        logo_html = ""
        
        try:
            import base64
            import os
            
            if os.path.exists(logo_path):
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                logo_html = f'''
                <div style="text-align: center; margin-bottom: 1rem;">
                    <img src="data:image/png;base64,iVB0Rw0KGgoAAAANSUhEUg..." 
                         alt="HalalBot Logo" 
                         style="height: 80px; width: auto; border-radius: 10px;">
                </div>
                '''
            else:
                # Fallback to text logo
                logo_html = '''
                <div style="text-align: center; margin-bottom: 1rem;">
                    <div style="
                        display: inline-block;
                        background: rgba(255,255,255,0.2);
                        padding: 1rem 2rem;
                        border-radius: 15px;
                        font-size: 2rem;
                        font-weight: bold;
                    ">☪️ HalalBot</div>
                </div>
                '''
        except Exception:
            # Fallback if anything goes wrong
            logo_html = '''
            <div style="text-align: center; margin-bottom: 1rem;">
                <div style="font-size: 3rem;">☪️</div>
            </div>
            '''
        
        welcome_html = f"""
        <div style="
            background: linear-gradient(135deg, #1B5E3F 0%, #2E7D4A 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            {logo_html}
            <h2 style="margin: 0; font-family: 'Amiri', serif;">As-Salamu Alaikum!</h2>
            <p style="margin: 1rem 0 0 0; font-size: 1.1rem;">
                Welcome to HalalBot, your Islamic knowledge companion. 
                Ask me anything about Islam, and I'll provide guidance based on the Quran, 
                Hadith, and scholarly consensus.
            </p>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.95rem; opacity: 0.9;">
                🧠 <em>Note: I am an AI assistant trained on the Qur'an, Hadith, and select scholarly sources.</em><br>
                Please consult your local Imam or a qualified scholar for specific religious rulings.
            </p>
        </div>
        """
        
        st.markdown(welcome_html, unsafe_allow_html=True)
        
        # Conversation starters
        st.markdown("**💬 You can ask me about:**")
        
        cols = st.columns(3)
        starters = [
            "🕌 Prayer guidance", "💰 Zakat calculation", "🕋 Hajj preparation",
            "👨‍👩‍👧‍👦 Family matters", "💼 Business ethics", "📖 Quran interpretation"
        ]
        
        for i, starter in enumerate(starters):
            with cols[i % 3]:
                if st.button(starter, key=f"starter_{i}"):
                    starter_queries = {
                        "🕌 Prayer guidance": "How should I maintain my five daily prayers?",
                        "💰 Zakat calculation": "How do I calculate zakat on my wealth?",
                        "🕋 Hajj preparation": "What should I know about preparing for Hajj?",
                        "👨‍👩‍👧‍👦 Family matters": "What are the rights and responsibilities in a Muslim family?",
                        "💼 Business ethics": "What are the Islamic principles for conducting business?",
                        "📖 Quran interpretation": "How should I approach understanding the Quran?"
                    }
                    self.process_user_query(starter_queries[starter])

    def display_chat_history(self):
        """Display the conversation history in chat format"""
        
        if not st.session_state.chat_history:
            return
        
        # Create scrollable chat container
        chat_container = st.container()
        
        with chat_container:
            for exchange in st.session_state.chat_history:
                # User message
                self.display_user_message(exchange['user_query'])
                
                # AI response
                self.display_ai_response(exchange['ai_response'])
                
                # Separator
                st.markdown("---")

    def display_user_message(self, query: str):
        """Display user message with styling"""
        
        user_html = f"""
        <div style="
            display: flex;
            justify-content: flex-end;
            margin: 1rem 0;
        ">
            <div style="
                background: #E8F5E8;
                color: #1B5E3F;
                padding: 1rem 1.5rem;
                border-radius: 18px 18px 5px 18px;
                max-width: 70%;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                👤 {query}
            </div>
        </div>
        """
        
        st.markdown(user_html, unsafe_allow_html=True)

    def display_ai_response(self, response: Dict):
        """Display AI response with rich formatting"""
        
        # Main response bubble
        response_html = f"""
        <div style="
            display: flex;
            justify-content: flex-start;
            margin: 1rem 0;
        ">
            <div style="
                background: white;
                color: #2D3748;
                padding: 1.5rem;
                border-radius: 18px 18px 18px 5px;
                max-width: 85%;
                border-left: 4px solid #1B5E3F;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                line-height: 1.6;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.2rem;">🤖</span>
                    <strong style="margin-left: 0.5rem; color: #1B5E3F;">HalalBot</strong>
                </div>
                {response['main_answer'].replace(chr(10), '<br>')}
            </div>
        </div>
        """
        
        st.markdown(response_html, unsafe_allow_html=True)
        
        # Conversational Feedback Section
        self.display_conversational_feedback(response)
        
        # Additional elements in expandable sections
        if response.get('islamic_guidance'):
            with st.expander("🕌 Islamic Guidance"):
                st.write(response['islamic_guidance'])
        
        if response.get('related_topics'):
            with st.expander("🔗 Related Topics"):
                cols = st.columns(len(response['related_topics']))
                for i, topic in enumerate(response['related_topics']):
                    with cols[i]:
                        if st.button(f"📚 {topic}", key=f"related_{len(st.session_state.chat_history)}_{i}"):
                            self.process_user_query(f"Tell me about {topic}")
        
        if response.get('sources'):
            with st.expander("📖 Sources Used"):
                for i, source in enumerate(response['sources']):
                    source_icon = {'quran': '📖', 'hadith': '📜', 'fatwa': '⚖️'}.get(source['category'], '📚')
                    st.write(f"**{source_icon} {source['source']}** (Relevance: {source['score']:.2f})")
                    st.caption(source['text'])

    def display_conversational_feedback(self, response: Dict):
        """Display feedback for the conversational response"""
        
        # Unique key for this response
        response_id = f"response_{len(st.session_state.chat_history)}_{hash(response['main_answer'][:50])}"
        
        # Feedback container with Islamic styling
        feedback_html = """
        <div style="
            background: linear-gradient(135deg, #F7FAFC 0%, #EDF2F7 100%);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #E2E8F0;
        ">
        """
        
        st.markdown(feedback_html, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button(
                "👍 Helpful",
                key=f"helpful_{response_id}",
                help="This guidance was beneficial"
            ):
                self.log_conversational_feedback(response, "helpful", "Response was helpful")
                st.success("جزاك الله خيراً (May Allah reward you with good)")
        
        with col2:
            if st.button(
                "👎 Not Helpful",
                key=f"not_helpful_{response_id}",
                help="This guidance needs improvement"
            ):
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
        
        st.markdown('</div>', unsafe_allow_html=True)

    def log_conversational_feedback(self, response: Dict, feedback_type: str, details: str):
        """Log feedback for conversational responses"""
        
        from core.feedback import log_feedback
        from utils.logging import log_user_activity
        
        # Extract the user's original query from the response or session state
        original_query = response.get('query', 'Unknown query')
        
        # Log the feedback with enhanced details for conversational responses
        log_feedback(
            query=original_query,
            text=response['main_answer'][:500],  # First 500 chars for identification
            vote="up" if feedback_type == "helpful" else "down",
            user_email=st.session_state.email
        )
        
        # Log detailed user activity for conversational feedback
        log_user_activity(
            st.session_state.email,
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

    def categorize_query(self, query: str) -> str:
        """Categorize query for analytics"""
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

    def handle_chat_input(self):
        """Handle user input with chat-style interface"""
        
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

    def process_user_query(self, query: str):
        """Process user query and generate conversational response"""
        
        # Check for blocked content
        if is_blocked_query(query):
            st.error("⛔ This question is inappropriate and will not be processed. Please respect the sacred nature of this service.")
            log_blocked_query(st.session_state.email, query)
            return
        
        # Show processing indicator
        with st.spinner("🔍 Searching Islamic sources..."):
            
            try:
                # Get conversational response
                response = search_conversational(
                    query=query,
                    user_email=st.session_state.email,
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
                log_query_for_user(st.session_state.email, query, response.get('sources', []))
                
                # Rerun to display new message
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ I apologize, but I encountered an error: {str(e)}")
                st.info("💡 Please try rephrasing your question or contact support if the issue persists.")

    def display_follow_up_buttons(self):
        """Display follow-up question buttons"""
        
        if st.session_state.pending_follow_ups:
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
                        st.session_state.pending_follow_ups = []  # Clear after use

    def display_quick_topics(self):
        """Display quick topic access buttons"""
        
        if st.session_state.conversation_started:
            with st.expander("🚀 Quick Topics"):
                st.markdown("**Jump to popular topics:**")
                
                quick_topics = {
                    "🕌 Prayer times and conditions": "What are the conditions for valid prayer?",
                    "💰 Zakat calculation": "How do I calculate zakat on my savings?",
                    "🌙 Ramadan guidance": "What should I know about fasting in Ramadan?",
                    "💒 Marriage guidance": "What are the Islamic requirements for marriage?",
                    "📿 Daily duas": "What are some important daily supplications?",
                    "🤲 Making dua": "How should I make dua effectively?"
                }
                
                cols = st.columns(2)
                for i, (topic, query) in enumerate(quick_topics.items()):
                    with cols[i % 2]:
                        if st.button(topic, key=f"quick_topic_{i}"):
                            self.process_user_query(query)

    def display_conversation_controls(self):
        """Display conversation management controls"""
        
        if st.session_state.chat_history:
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

    def export_conversation(self):
        """Export conversation history"""
        
        if not st.session_state.chat_history:
            st.warning("No conversation to export.")
            return
        
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

    def show_feedback_form(self):
        """Show conversation feedback form"""
        
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


# Main function to integrate with the existing app
def create_conversational_search_interface():
    """
    Create the conversational search interface
    This replaces the traditional search interface
    """
    
    # Apply conversational styling
    st.markdown("""
    <style>
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 1rem;
        border-radius: 10px;
        background: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize and display chat interface
    chat_interface = ConversationalChatInterface()
    chat_interface.display_chat_interface()
    chat_interface.display_conversation_controls()


# For testing the interface
if __name__ == "__main__":
    # This would be called from your main app.py instead of the old search interface
    create_conversational_search_interface()
