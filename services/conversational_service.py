# services/conversational_service.py
"""
Conversational Islamic AI Service for HalalBot
BRIDGE VERSION: Works with your existing search infrastructure

This version integrates with your existing search_service.py file
and adds conversational capabilities on top of it.
"""

import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Import your existing search service
try:
    from services.search_service import search_faiss, DatabaseSearchService
    SEARCH_SERVICE_AVAILABLE = True
except ImportError:
    print("Warning: search_service not found, using fallback")
    SEARCH_SERVICE_AVAILABLE = False

# Import text processing
try:
    from utils.text_processing import clean_text
except ImportError:
    # Fallback clean function
    def clean_text(text, source_type=None):
        return text.strip() if text else ""

class IslamicConversationalAI:
    """
    Conversational AI that transforms your existing search results 
    into natural, contextual Islamic guidance
    """
    
    def __init__(self):
        self.conversation_history = {}
        self.context_window = 5  # Remember last 5 exchanges
        
        # Islamic greeting patterns and responses
        self.islamic_greetings = {
            'assalamu alaikum': 'Wa alaikum assalam wa rahmatullahi wa barakatuh',
            'assalam alaikum': 'Wa alaikum assalam wa rahmatullahi wa barakatuh',
            'peace be upon you': 'And upon you peace',
            'salam': 'Wa alaikum assalam'
        }
        
        # Common follow-up templates based on topics
        self.follow_up_templates = {
            'prayer': [
                "Would you like to know about specific prayer times?",
                "Do you have questions about prayer conditions or requirements?",
                "Would you like guidance on how to perform specific prayers?"
            ],
            'zakat': [
                "Would you like help calculating your zakat?",
                "Do you have questions about what assets require zakat?",
                "Would you like to know about zakat distribution?"
            ],
            'hajj': [
                "Are you planning to perform Hajj soon?",
                "Would you like to know about Hajj preparations?",
                "Do you have questions about specific Hajj rituals?"
            ],
            'marriage': [
                "Are you seeking guidance for your own situation?",
                "Would you like to know about Islamic marriage contracts?",
                "Do you have questions about marital rights and responsibilities?"
            ],
            'fasting': [
                "Are you preparing for Ramadan?",
                "Would you like to know about voluntary fasting?",
                "Do you have questions about breaking fast (iftar)?"
            ]
        }

    def generate_conversational_response(
        self, 
        user_query: str, 
        user_email: str,
        search_results: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        Transform search results into conversational Islamic guidance
        
        Args:
            user_query: The user's question
            user_email: User identifier for conversation history
            search_results: Results from your existing search service
            context: Optional conversation context
            
        Returns:
            Structured conversational response
        """
        
        # Handle Islamic greetings
        greeting_response = self._handle_greetings(user_query)
        if greeting_response:
            return self._create_response(
                main_answer=greeting_response,
                query=user_query,
                response_type="greeting"
            )
        
        # Get conversation context
        conversation_context = self._get_conversation_context(user_email)
        
        # Synthesize main answer from search results
        main_answer = self._synthesize_answer(user_query, search_results, conversation_context)
        
        # Generate follow-up questions
        follow_ups = self._generate_follow_ups(user_query, search_results)
        
        # Add Islamic guidance and etiquette
        islamic_guidance = self._add_islamic_guidance(user_query, search_results)
        
        # Suggest related topics
        related_topics = self._suggest_related_topics(user_query, search_results)
        
        # Update conversation history
        self._update_conversation_history(user_email, user_query, main_answer)
        
        return self._create_response(
            main_answer=main_answer,
            follow_ups=follow_ups,
            islamic_guidance=islamic_guidance,
            related_topics=related_topics,
            sources=search_results,
            query=user_query,
            response_type="comprehensive"
        )

    def _handle_greetings(self, query: str) -> Optional[str]:
        """Handle Islamic greetings appropriately"""
        query_lower = query.lower()
        
        for greeting, response in self.islamic_greetings.items():
            if greeting in query_lower:
                return f"{response}! How may I assist you with your Islamic knowledge today? Feel free to ask me anything about prayer, zakat, Hajj, family matters, or any other Islamic topic."
        
        return None

    def _synthesize_answer(
        self, 
        query: str, 
        results: List[Dict], 
        context: Optional[Dict] = None
    ) -> str:
        """
        Transform your search results into natural, conversational guidance
        """
        if not results:
            return self._generate_no_results_response(query)
        
        # Determine the topic/category
        primary_category = self._determine_primary_category(results)
        
        # Create contextual introduction
        intro = self._create_contextual_intro(query, primary_category)
        
        # Synthesize core content from top results
        core_content = self._synthesize_core_content(results[:3])
        
        # Add Quranic/Hadith emphasis if available
        scriptural_emphasis = self._add_scriptural_emphasis(results)
        
        # Conclude with Islamic etiquette
        conclusion = self._create_islamic_conclusion(primary_category)
        
        return f"{intro}\n\n{core_content}{scriptural_emphasis}\n\n{conclusion}"

    def _create_contextual_intro(self, query: str, category: str) -> str:
        """Create a personalized introduction based on the query"""
        
        intro_templates = {
            'quran': "Regarding your question about Quranic guidance",
            'hadith': "Concerning the Prophetic teachings (Hadith)",
            'prayer': "Regarding your question about prayer (salah)",
            'zakat': "Concerning zakat and charitable obligations",
            'hajj': "About the pilgrimage (Hajj)",
            'marriage': "Regarding marriage in Islam",
            'fasting': "Concerning fasting (sawm)",
            'fatwa': "Regarding the scholarly ruling you asked about",
            'general': "In response to your question"
        }
        
        template = intro_templates.get(category, intro_templates['general'])
        
        # Add personalization based on query tone
        if '?' in query:
            return f"{template}, I understand you're seeking guidance."
        elif any(word in query.lower() for word in ['help', 'explain', 'clarify']):
            return f"{template}, I'm here to help you understand."
        else:
            return f"{template}, here's what Islamic teachings tell us:"

    def _synthesize_core_content(self, top_results: List[Dict]) -> str:
        """Synthesize the main content from your search results"""
        
        if not top_results:
            return ""
        
        # Group by source type for better organization
        quran_content = []
        hadith_content = []
        scholarly_content = []
        
        for result in top_results:
            category = result.get('category', '').lower()
            text = result.get('text', '')
            
            if category == 'quran':
                quran_content.append(text)
            elif category == 'hadith':
                hadith_content.append(text)
            else:
                scholarly_content.append(text)
        
        # Build synthesized response prioritizing Islamic sources
        response_parts = []
        
        # Start with Quranic guidance if available (highest authority)
        if quran_content:
            clean_quran = clean_text(quran_content[0], 'quran')
            response_parts.append(f"The Quran guides us: {clean_quran}")
        
        # Add Prophetic guidance (second highest authority)
        if hadith_content:
            clean_hadith = clean_text(hadith_content[0], 'hadith')
            response_parts.append(f"The Prophet (ﷺ) taught us: {clean_hadith}")
        
        # Add scholarly interpretation
        if scholarly_content:
            clean_scholarly = clean_text(scholarly_content[0])
            response_parts.append(f"Islamic scholars explain: {clean_scholarly}")
        
        # If no specific sources, use the best result
        if not response_parts and top_results:
            best_result = clean_text(top_results[0].get('text', ''))
            response_parts.append(f"Based on Islamic teachings: {best_result}")
        
        return "\n\n".join(response_parts)

    def _add_scriptural_emphasis(self, results: List[Dict]) -> str:
        """Add emphasis when Quran or authentic Hadith are involved"""
        
        has_quran = any(r.get('category') == 'quran' for r in results)
        has_hadith = any(r.get('category') == 'hadith' for r in results)
        
        if has_quran and has_hadith:
            return "\n\n*This guidance is supported by both the Quran and authentic Hadith.*"
        elif has_quran:
            return "\n\n*This is direct guidance from the Holy Quran.*"
        elif has_hadith:
            return "\n\n*This is based on authentic Prophetic tradition.*"
        
        return ""

    def _create_islamic_conclusion(self, category: str) -> str:
        """Add appropriate Islamic conclusion with du'a"""
        
        conclusions = {
            'quran': "May Allah guide us to follow His divine guidance faithfully.",
            'hadith': "May Allah grant us the ability to follow the Sunnah of His Messenger (ﷺ).",
            'prayer': "May Allah accept your prayers and grant you consistency in worship.",
            'zakat': "May Allah accept your charity and purify your wealth.",
            'hajj': "May Allah grant you a blessed and accepted pilgrimage.",
            'marriage': "May Allah bless your marriage and grant you righteousness.",
            'fasting': "May Allah accept your fasting and grant you taqwa.",
            'fatwa': "May Allah guide you to what is correct and most pleasing to Him.",
            'general': "May Allah guide you to what is best and increase you in beneficial knowledge."
        }
        
        conclusion = conclusions.get(category, conclusions['general'])
        return f"{conclusion}\n\nWallahu a'lam (And Allah knows best)."

    def _generate_follow_ups(self, query: str, results: List[Dict]) -> List[str]:
        """Generate contextual follow-up questions"""
        
        # Determine main topic
        topic = self._extract_main_topic(query, results)
        
        # Get topic-specific follow-ups
        topic_follow_ups = self.follow_up_templates.get(topic, [])
        
        # Add general follow-ups
        general_follow_ups = [
            "Would you like more specific guidance on this topic?",
            "Do you have any particular circumstances I should consider?",
            "Would you like to know about common misconceptions regarding this?"
        ]
        
        # Combine and limit to 3 most relevant
        all_follow_ups = topic_follow_ups + general_follow_ups
        return all_follow_ups[:3]

    def _add_islamic_guidance(self, query: str, results: List[Dict]) -> Optional[str]:
        """Add relevant Islamic guidance and etiquette"""
        
        guidance_map = {
            'prayer': "Remember that consistency in prayer is more beloved to Allah than occasional lengthy prayers. Even if you miss a prayer, make it up as soon as you remember.",
            'zakat': "Giving charity purifies both your wealth and your soul. It's not just about the amount, but the sincerity and regularity of giving.",
            'marriage': "Marriage is half of faith when approached with sincerity and fear of Allah. Focus on compatibility in faith and character.",
            'business': "All business dealings should be conducted with honesty, fairness, and transparency. Avoid any form of deception or exploitation.",
            'family': "Be kind to your parents and maintain family ties, as this is highly emphasized in Islam and brings Allah's blessings.",
            'fasting': "Fasting is not just about abstaining from food and drink, but also from bad speech, actions, and thoughts."
        }
        
        topic = self._extract_main_topic(query, results)
        return guidance_map.get(topic)

    def _suggest_related_topics(self, query: str, results: List[Dict]) -> List[str]:
        """Suggest related topics the user might be interested in"""
        
        topic = self._extract_main_topic(query, results)
        
        related_topics_map = {
            'prayer': ['Prayer times', 'Ablution (Wudu)', 'Quran recitation', 'Du\'a after prayer'],
            'zakat': ['Sadaqah', 'Charity recipients', 'Wealth purification', 'Business ethics'],
            'hajj': ['Umrah', 'Islamic calendar', 'Du\'as for travel', 'Spiritual preparation'],
            'marriage': ['Family rights', 'Islamic parenting', 'Marital problems', 'Mahr (dower)'],
            'fasting': ['Ramadan preparation', 'Eid celebration', 'Voluntary fasting', 'Breaking fast etiquette']
        }
        
        return related_topics_map.get(topic, ['Islamic ethics', 'Daily supplications', 'Prophetic guidance'])

    def _determine_primary_category(self, results: List[Dict]) -> str:
        """Determine the primary category based on your search results"""
        
        if not results:
            return 'general'
        
        # Count categories in results
        category_counts = {}
        for result in results:
            category = result.get('category', 'other')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Return most common category
        return max(category_counts, key=category_counts.get) if category_counts else 'general'

    def _extract_main_topic(self, query: str, results: List[Dict]) -> str:
        """Extract the main topic from query and results"""
        
        query_lower = query.lower()
        
        # Topic keywords mapping
        topic_keywords = {
            'prayer': ['prayer', 'salah', 'namaz', 'pray', 'worship', 'wudu', 'ablution'],
            'zakat': ['zakat', 'charity', 'alms', 'wealth', 'money', 'poor'],
            'hajj': ['hajj', 'pilgrimage', 'mecca', 'umrah', 'kaaba', 'tawaf'],
            'marriage': ['marriage', 'wedding', 'spouse', 'husband', 'wife', 'nikah'],
            'fasting': ['fasting', 'ramadan', 'sawm', 'iftar', 'suhur', 'fast'],
            'business': ['business', 'trade', 'work', 'job', 'income', 'money'],
            'family': ['family', 'parents', 'children', 'relatives', 'mother', 'father']
        }
        
        # Check query for topic keywords
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic
        
        # Check results categories
        if results:
            return self._determine_primary_category(results)
        
        return 'general'

    def _get_conversation_context(self, user_email: str) -> Optional[Dict]:
        """Get recent conversation history for context"""
        return self.conversation_history.get(user_email, {})

    def _update_conversation_history(self, user_email: str, query: str, response: str):
        """Update conversation history for continuity"""
        
        if user_email not in self.conversation_history:
            self.conversation_history[user_email] = {'exchanges': [], 'topics': set()}
        
        history = self.conversation_history[user_email]
        
        # Add current exchange
        history['exchanges'].append({
            'query': query,
            'response': response[:200] + "..." if len(response) > 200 else response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent exchanges
        if len(history['exchanges']) > self.context_window:
            history['exchanges'] = history['exchanges'][-self.context_window:]
        
        # Track topics discussed
        topic = self._extract_main_topic(query, [])
        history['topics'].add(topic)

    def _generate_no_results_response(self, query: str) -> str:
        """Generate a helpful response when no search results are found"""
        
        return f"""I apologize, but I couldn't find specific guidance on "{query}" in my current knowledge base. 

However, I encourage you to:

**📚 Consult authentic sources:** Please reach out to your local Imam or a qualified Islamic scholar who can provide personalized guidance based on your specific circumstances.

**🔄 Try rephrasing:** Sometimes asking the question in a different way can yield better results. You might try:
- Using simpler terms
- Being more specific about your situation
- Adding context about what you're trying to understand

**🕌 Remember the fundamentals:** Even when specific guidance isn't available, the core Islamic principles of following Allah's guidance, being just, showing compassion, and seeking beneficial knowledge can help guide your decisions.

May Allah guide you to the correct path and grant you beneficial knowledge.

Wallahu a'lam (And Allah knows best)."""

    def _create_response(
        self, 
        main_answer: str,
        query: str,
        response_type: str = "comprehensive",
        follow_ups: List[str] = None,
        islamic_guidance: str = None,
        related_topics: List[str] = None,
        sources: List[Dict] = None
    ) -> Dict[str, any]:
        """Create the final structured response"""
        
        response = {
            'main_answer': main_answer,
            'query': query,
            'response_type': response_type,
            'timestamp': datetime.now().isoformat()
        }
        
        if follow_ups:
            response['follow_up_questions'] = follow_ups
        
        if islamic_guidance:
            response['islamic_guidance'] = islamic_guidance
            
        if related_topics:
            response['related_topics'] = related_topics
            
        if sources:
            response['sources'] = [
                {
                    'text': s.get('text', '')[:200] + '...',
                    'source': s.get('source', 'Unknown'),
                    'category': s.get('category', 'other'),
                    'score': s.get('score', 0)
                }
                for s in sources[:3]  # Limit to top 3 sources
            ]
        
        return response


def search_conversational(
    query: str,
    user_email: str,
    top_k: int = 5,
    min_score: float = 0.5,
    source_filter: Optional[str] = None
) -> Dict[str, any]:
    """
    Main function: Bridge between your existing search and conversational AI
    
    Args:
        query: User's question
        user_email: User identifier
        top_k: Number of search results to retrieve
        min_score: Minimum similarity score
        source_filter: Optional source filter
        
    Returns:
        Conversational response with synthesized answer
    """
    
    # Initialize conversational AI
    conv_ai = IslamicConversationalAI()
    
    # Use your existing search service
    if SEARCH_SERVICE_AVAILABLE:
        search_results = search_faiss(query, top_k, min_score, source_filter)
    else:
        # Fallback if search service not available
        search_results = []
    
    # Generate conversational response
    response = conv_ai.generate_conversational_response(
        user_query=query,
        user_email=user_email,
        search_results=search_results
    )
    
    return response


# Backwards compatibility with your existing code
def format_markdown_response(query: str, results: List[Dict]) -> str:
    """
    Convert conversational response back to markdown for compatibility
    Used if you want to gradually transition from old to new interface
    """
    
    if not results:
        return f"\n**🔍 Query:** _{query}_\n\n_No relevant answers found._"
    
    # For backwards compatibility, just use the first result as main response
    main_result = results[0] if results else {}
    main_text = main_result.get('main_answer', main_result.get('text', ''))
    
    output = f"\n**🔍 Query:** _{query}_\n\n"
    output += f"**🤖 HalalBot:** {main_text}\n\n"
    
    # Add sources if available
    if 'sources' in main_result:
        output += "**📖 Sources:**\n"
        for source in main_result['sources']:
            output += f"• {source['source']} (Score: {source['score']:.2f})\n"
    
    return output


# Testing function
def test_conversational_service():
    """Test the conversational service"""
    
    print("🧪 Testing Conversational Islamic AI Service...")
    
    test_queries = [
        "How do I perform wudu?",
        "What is zakat calculation?", 
        "Assalamu alaikum, can you help me?",
        "Marriage guidance in Islam"
    ]
    
    try:
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            response = search_conversational(query, "test@example.com")
            print(f"✅ Response type: {response['response_type']}")
            print(f"📝 Answer preview: {response['main_answer'][:100]}...")
            
            if response.get('follow_up_questions'):
                print(f"🤔 Follow-ups: {len(response['follow_up_questions'])}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_conversational_service()