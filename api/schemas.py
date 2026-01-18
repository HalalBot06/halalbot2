# api/schemas.py
"""
HalalBot API Data Schemas

Pydantic models defining request/response structures for the REST API.
These ensure type safety and automatic validation for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============================================================================
# CHAT ENDPOINT SCHEMAS
# ============================================================================

class ChatRequest(BaseModel):
    """
    Request body for the /api/chat endpoint
    Sent by iOS app when user asks a question
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User's question about Islamic knowledge",
        examples=["How do I perform wudu?", "What is the nisab for zakat?"]
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User identifier for conversation history"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for context continuity"
    )
    source_filter: Optional[str] = Field(
        default=None,
        description="Filter results by source: quran-only, hadith-only, fatwa-only, zakat-only",
        examples=["quran-only", "hadith-only"]
    )


class SourceDocument(BaseModel):
    """
    A source document used to generate the response
    """
    text: str = Field(..., description="Document text content")
    source: str = Field(..., description="Source type: quran, hadith, fatwa, zakat, other")
    title: Optional[str] = Field(default=None, description="Document title if available")
    category: str = Field(..., description="Document category")
    similarity_score: float = Field(..., description="Relevance score (0.0 to 1.0)")


class ChatResponse(BaseModel):
    """
    Response body from the /api/chat endpoint
    Returned to iOS app with synthesized answer
    """
    success: bool = Field(..., description="Whether the request was successful")
    query: str = Field(..., description="Original query (echoed back)")
    answer: str = Field(..., description="Synthesized conversational answer")
    sources: List[SourceDocument] = Field(
        default=[],
        description="Source documents used to generate the answer"
    )
    follow_up_questions: List[str] = Field(
        default=[],
        description="Suggested follow-up questions"
    )
    islamic_greeting: Optional[str] = Field(
        default=None,
        description="Islamic greeting response if query was a greeting"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for continuing the chat"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if success is False"
    )


# ============================================================================
# SEARCH ENDPOINT SCHEMAS (Raw search without synthesis)
# ============================================================================

class SearchRequest(BaseModel):
    """
    Request body for the /api/search endpoint
    For raw semantic search without conversational synthesis
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of results to return"
    )
    min_score: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold"
    )
    source_filter: Optional[str] = Field(
        default=None,
        description="Filter by source type"
    )


class SearchResponse(BaseModel):
    """
    Response body from the /api/search endpoint
    """
    success: bool = Field(..., description="Whether the search was successful")
    query: str = Field(..., description="Original query")
    results: List[SourceDocument] = Field(
        default=[],
        description="Search results ranked by relevance"
    )
    total_found: int = Field(..., description="Total number of results found")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if success is False"
    )


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class AuthRequest(BaseModel):
    """
    Request body for the /api/auth endpoint
    """
    email: str = Field(
        ...,
        description="User email address"
    )
    invite_code: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Invite code for registration/login"
    )


class AuthResponse(BaseModel):
    """
    Response body from the /api/auth endpoint
    """
    success: bool = Field(..., description="Whether authentication succeeded")
    user_id: Optional[str] = Field(
        default=None,
        description="User ID if authenticated"
    )
    email: Optional[str] = Field(
        default=None,
        description="User email if authenticated"
    )
    token: Optional[str] = Field(
        default=None,
        description="Session token for subsequent requests"
    )
    is_admin: bool = Field(
        default=False,
        description="Whether user has admin privileges"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if success is False"
    )


# ============================================================================
# HEALTH CHECK SCHEMA
# ============================================================================

class HealthResponse(BaseModel):
    """
    Response body from the /api/health endpoint
    """
    status: str = Field(..., description="API status: healthy, degraded, or unhealthy")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Whether database is accessible")
    model_loaded: bool = Field(..., description="Whether sentence-transformer model is loaded")
    document_count: Optional[int] = Field(
        default=None,
        description="Number of documents in database"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )


# ============================================================================
# FEEDBACK SCHEMA (for user feedback on responses)
# ============================================================================

class FeedbackRequest(BaseModel):
    """
    Request body for submitting feedback on a response
    """
    conversation_id: str = Field(..., description="ID of the conversation")
    query: str = Field(..., description="The original query")
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 (poor) to 5 (excellent)"
    )
    feedback_text: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional written feedback"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID if authenticated"
    )


class FeedbackResponse(BaseModel):
    """
    Response body after submitting feedback
    """
    success: bool = Field(..., description="Whether feedback was recorded")
    message: str = Field(..., description="Confirmation message")