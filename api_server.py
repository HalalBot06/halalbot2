#!/usr/bin/env python3
"""
HalalBot API Server

Simple FastAPI server for the iOS app.
Runs as a separate Railway service from the Streamlit web app.
"""

import os
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import HealthResponse
from api.routes.chat import router as chat_router


# ============================================================================
# CONFIGURATION
# ============================================================================

PORT = int(os.environ.get("PORT", 8080))

app_state = {
    "database_connected": False,
    "model_loaded": False,
    "document_count": None,
}


# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    print("🚀 HalalBot API starting...")
    
    # Test database
    try:
        from config.database import get_db_manager
        db = get_db_manager()
        if db.health_check():
            app_state["database_connected"] = True
            result = db.execute_query(
                "SELECT COUNT(*) as count FROM documents",
                fetch=True, fetch_one=True
            )
            if result:
                app_state["document_count"] = result.get('count', 0)
            print(f"✅ Database connected - {app_state['document_count']:,} documents")
    except Exception as e:
        print(f"⚠️  Database error: {e}")
    
    # Test model
    try:
        from sentence_transformers import SentenceTransformer
        app_state["model_loaded"] = True
        print("✅ Model available")
    except Exception as e:
        print(f"⚠️  Model error: {e}")
    
    print("🕌 HalalBot API ready!")
    print(f"   • Docs: http://localhost:{PORT}/api/docs")
    
    yield
    
    print("👋 Shutting down...")
    try:
        from config.database import cleanup_database
        cleanup_database()
    except:
        pass


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HalalBot API",
    description="Islamic Knowledge Assistant REST API for iOS app",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS - allow iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include chat routes
app.include_router(chat_router)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """API information"""
    return {
        "name": "HalalBot API",
        "version": "1.0.0",
        "description": "Islamic Knowledge Assistant REST API",
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.get("/api", tags=["api"])
async def api_root():
    """API endpoints"""
    return {
        "name": "HalalBot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "search": "POST /api/search",
            "health": "GET /api/health",
        }
    }


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check"""
    status = "healthy" if app_state["database_connected"] and app_state["model_loaded"] else "degraded"
    return HealthResponse(
        status=status,
        version="1.0.0",
        database_connected=app_state["database_connected"],
        model_loaded=app_state["model_loaded"],
        document_count=app_state["document_count"],
        timestamp=datetime.utcnow()
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🕌 HalalBot API Server")
    print("=" * 50)
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info",
    )
