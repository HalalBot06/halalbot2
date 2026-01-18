# api/__init__.py
"""
HalalBot REST API Package

This package provides REST API endpoints for the HalalBot iOS app
and any other clients that need to access the Islamic knowledge search.

Endpoints:
- POST /api/chat    → Conversational Islamic guidance
- POST /api/search  → Raw semantic search results
- POST /api/auth    → User authentication
- GET  /api/health  → Health check
"""

__version__ = "1.0.0"