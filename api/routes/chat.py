# api/routes/chat.py
"""
HalalBot Chat API Endpoint

Main conversational endpoint for the iOS app.
Receives questions, searches the Islamic knowledge base,
and returns synthesized conversational answers.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException

# Import schemas
from api.schemas import (
    ChatRequest,
    ChatResponse,
    SourceDocument,
    SearchRequest,
    SearchResponse
)

# Create router
router = APIRouter(prefix="/api", tags=["chat"])


# ============================================================================
# ISLAMIC GREETING DETECTION
# ============================================================================

ISLAMIC_GREETINGS = {
    "assalamu alaikum": "Wa alaikum assalam wa rahmatullahi wa barakatuh! How may I help you today?",
    "assalam alaikum": "Wa alaikum assalam wa rahmatullahi wa barakatuh! How may I help you today?",
    "as-salamu alaykum": "Wa alaikum assalam wa rahmatullahi wa barakatuh! How may I help you today?",
    "salam": "Wa alaikum assalam! How may I help you today?",
    "peace be upon you": "And upon you be peace! How may I help you today?",
}


def check_islamic_greeting(query: str) -> Optional[str]:
    """Check if query is an Islamic greeting and return appropriate response"""
    query_lower = query.lower().strip()
    for greeting, response in ISLAMIC_GREETINGS.items():
        if greeting in query_lower:
            return response
    return None


# ============================================================================
# ANSWER SYNTHESIS
# ============================================================================

def get_source_emoji(source: str) -> str:
    """Get emoji for source type"""
    emojis = {
        "quran": "📖",
        "hadith": "📜",
        "fatwa": "⚖️",
        "zakat": "💰",
        "other": "📚"
    }
    return emojis.get(source.lower() if source else "other", "📚")


def synthesize_answer(query: str, search_results: list) -> str:
    """
    Synthesize a conversational answer from search results.
    
    This creates a natural, helpful response that:
    - Directly addresses the user's question
    - Incorporates information from the sources
    - Maintains an Islamic tone
    - Encourages consulting scholars for specific rulings
    """
    if not search_results:
        return (
            "I wasn't able to find specific information about that in my knowledge base. "
            "This might be a topic that requires consultation with a qualified Islamic scholar "
            "who can provide guidance based on your specific circumstances. "
            "Is there another way I can help you, or would you like to rephrase your question?"
        )
    
    # Group results by source type
    sources_used = {}
    for result in search_results[:5]:  # Use top 5 results
        source = result.get("source", "other") or "other"
        if source not in sources_used:
            sources_used[source] = []
        sources_used[source].append(result)
    
    # Build the answer
    answer_parts = []
    
    # Opening that acknowledges the question
    answer_parts.append(f"Regarding your question about **{query}**:\n")
    
    # Add content from each source type (prioritized)
    source_priority = ["quran", "hadith", "fatwa", "zakat", "other"]
    
    for source_type in source_priority:
        if source_type in sources_used:
            results = sources_used[source_type]
            emoji = get_source_emoji(source_type)
            source_name = source_type.title()
            
            if source_type == "quran":
                answer_parts.append(f"\n{emoji} **From the Quran:**")
            elif source_type == "hadith":
                answer_parts.append(f"\n{emoji} **From the Hadith:**")
            elif source_type == "fatwa":
                answer_parts.append(f"\n{emoji} **Scholarly Guidance:**")
            elif source_type == "zakat":
                answer_parts.append(f"\n{emoji} **Regarding Zakat:**")
            else:
                answer_parts.append(f"\n{emoji} **Additional Information:**")
            
            # Add the most relevant result from this source
            top_result = results[0]
            text = top_result.get("text", "").strip()
            
            # Truncate very long texts
            if len(text) > 500:
                text = text[:500] + "..."
            
            answer_parts.append(f"\n{text}")
    
    # Add closing guidance
    answer_parts.append(
        "\n\n---\n"
        "*For specific rulings applicable to your situation, please consult with a qualified "
        "Islamic scholar or your local imam who can provide personalized guidance.*"
    )
    
    return "\n".join(answer_parts)


def generate_follow_up_questions(query: str, search_results: list) -> list:
    """Generate relevant follow-up questions based on the topic"""
    query_lower = query.lower()
    follow_ups = []
    
    # Topic-based follow-ups
    if any(word in query_lower for word in ["prayer", "salah", "salat", "pray"]):
        follow_ups = [
            "What are the conditions for valid prayer?",
            "How do I make up missed prayers?",
            "What invalidates the prayer?"
        ]
    elif any(word in query_lower for word in ["wudu", "ablution", "wash"]):
        follow_ups = [
            "What breaks wudu?",
            "What is tayammum and when is it permitted?",
            "What are the obligatory acts of wudu?"
        ]
    elif any(word in query_lower for word in ["zakat", "charity", "sadaqah"]):
        follow_ups = [
            "How do I calculate my zakat?",
            "What is the nisab threshold?",
            "Who is eligible to receive zakat?"
        ]
    elif any(word in query_lower for word in ["fast", "fasting", "ramadan", "sawm"]):
        follow_ups = [
            "What breaks the fast?",
            "Who is exempt from fasting?",
            "What is the fidyah for missed fasts?"
        ]
    elif any(word in query_lower for word in ["hajj", "umrah", "pilgrimage", "mecca"]):
        follow_ups = [
            "What are the pillars of Hajj?",
            "What is the difference between Hajj and Umrah?",
            "What preparations are needed for Hajj?"
        ]
    elif any(word in query_lower for word in ["marriage", "nikah", "wedding", "spouse"]):
        follow_ups = [
            "What are the conditions for a valid nikah?",
            "What is the mahr (dowry)?",
            "What are the rights of spouses in Islam?"
        ]
    elif any(word in query_lower for word in ["halal", "haram", "food", "eat"]):
        follow_ups = [
            "What makes food halal?",
            "What animals are permissible to eat?",
            "Is seafood halal?"
        ]
    else:
        # Generic follow-ups
        follow_ups = [
            "Would you like more details on this topic?",
            "Are there related topics you'd like to explore?",
            "Do you have a specific situation you need guidance on?"
        ]
    
    return follow_ups[:3]  # Return max 3 follow-ups


# ============================================================================
# CHAT ENDPOINT
# ============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for conversational Islamic guidance.
    
    Receives a question, searches the knowledge base, and returns
    a synthesized conversational answer with sources.
    """
    try:
        query = request.query.strip()
        
        # Check for Islamic greeting first
        greeting_response = check_islamic_greeting(query)
        if greeting_response:
            return ChatResponse(
                success=True,
                query=query,
                answer=greeting_response,
                sources=[],
                follow_up_questions=[
                    "How do I perform wudu correctly?",
                    "What are the five pillars of Islam?",
                    "How do I calculate my zakat?"
                ],
                islamic_greeting=greeting_response,
                conversation_id=request.conversation_id or str(uuid.uuid4()),
                timestamp=datetime.utcnow()
            )
        
        # Import search service (done here to avoid circular imports)
        try:
            from services.search_service import search_faiss
        except ImportError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search service not available: {str(e)}"
            )
        
        # Perform semantic search
        search_results = search_faiss(
            query=query,
            top_k=10,
            min_score=0.5,  # Low threshold - semantic scores are 0.05-0.27 for good matches
            source_filter=request.source_filter
        )
        
        # Convert results to SourceDocument objects
        source_documents = []
        for result in search_results:
            source_documents.append(SourceDocument(
                text=result.get("text", "")[:500],  # Truncate for response
                source=result.get("source", "other") or "other",
                title=result.get("title"),
                category=result.get("category", "other"),
                similarity_score=result.get("score", 0.0)
            ))
        
        # Synthesize conversational answer
        answer = synthesize_answer(query, search_results)
        
        # Generate follow-up questions
        follow_ups = generate_follow_up_questions(query, search_results)
        
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        return ChatResponse(
            success=True,
            query=query,
            answer=answer,
            sources=source_documents,
            follow_up_questions=follow_ups,
            conversation_id=conversation_id,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(
            success=False,
            query=request.query,
            answer="I apologize, but I encountered an error processing your question. Please try again.",
            sources=[],
            follow_up_questions=[],
            error_message=str(e),
            timestamp=datetime.utcnow()
        )


# ============================================================================
# RAW SEARCH ENDPOINT (for advanced users)
# ============================================================================

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Raw semantic search endpoint.
    
    Returns search results without conversational synthesis.
    Useful for debugging or advanced integrations.
    """
    try:
        # Import search service
        try:
            from services.search_service import search_faiss
        except ImportError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Search service not available: {str(e)}"
            )
        
        # Perform search
        search_results = search_faiss(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score,
            source_filter=request.source_filter
        )
        
        # Convert to response format
        results = []
        for result in search_results:
            results.append(SourceDocument(
                text=result.get("text", ""),
                source=result.get("source", "other") or "other",
                title=result.get("title"),
                category=result.get("category", "other"),
                similarity_score=result.get("score", 0.0)
            ))
        
        return SearchResponse(
            success=True,
            query=request.query,
            results=results,
            total_found=len(results),
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return SearchResponse(
            success=False,
            query=request.query,
            results=[],
            total_found=0,
            error_message=str(e),
            timestamp=datetime.utcnow()
        )
