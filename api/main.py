# api/main.py
"""
HalalBot REST API

FastAPI application providing REST endpoints for the iOS app
and other clients to access Islamic knowledge search.

Run locally:
    uvicorn api.main:app --reload --port 8000

Run on Railway (alongside Streamlit):
    See Procfile configuration
"""

import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import schemas
from api.schemas import HealthResponse

# Import routes
from api.routes.chat import router as chat_router


# ============================================================================
# STARTUP / SHUTDOWN EVENTS
# ============================================================================

# Global state for health checks
app_state = {
    "database_connected": False,
    "model_loaded": False,
    "document_count": None,
    "startup_time": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the API.
    Initializes database connection and loads the ML model.
    """
    # === STARTUP ===
    print("🚀 HalalBot API starting up...")
    app_state["startup_time"] = datetime.utcnow()
    
    # Test database connection
    try:
        from config.database import get_db_connection
        conn = get_db_connection()
        if conn:
            # Get document count
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            app_state["document_count"] = count
            app_state["database_connected"] = True
            cursor.close()
            conn.close()
            print(f"✅ Database connected - {count:,} documents available")
        else:
            print("⚠️  Database connection returned None")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        app_state["database_connected"] = False
    
    # Test model loading
    try:
        from sentence_transformers import SentenceTransformer
        # Just verify the model can be imported - actual loading happens in search_service
        app_state["model_loaded"] = True
        print("✅ Sentence transformer model available")
    except Exception as e:
        print(f"⚠️  Model loading failed: {e}")
        app_state["model_loaded"] = False
    
    print("🕌 HalalBot API ready to serve!")
    
    yield  # App runs here
    
    # === SHUTDOWN ===
    print("👋 HalalBot API shutting down...")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HalalBot API",
    description=(
        "REST API for HalalBot Islamic Knowledge Assistant.\n\n"
        "Provides semantic search across 29,000+ Islamic documents including "
        "Quran verses, Hadith collections, Fatwa rulings, and Zakat guidance.\n\n"
        "**Endpoints:**\n"
        "- `POST /api/chat` - Conversational Islamic guidance\n"
        "- `POST /api/search` - Raw semantic search\n"
        "- `GET /api/health` - Health check\n"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",      # Swagger UI at /api/docs
    redoc_url="/api/redoc",    # ReDoc at /api/redoc
    openapi_url="/api/openapi.json"
)


# ============================================================================
# CORS MIDDLEWARE (allows iOS app to connect)
# ============================================================================

# Get allowed origins from environment or use defaults
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [""]:
    ALLOWED_ORIGINS = [
        "http://localhost:3000",        # Local development
        "http://localhost:8080",        # Local Streamlit
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "https://halalbot2-production.up.railway.app",  # Your Railway app
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

app.include_router(chat_router)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns the current status of the API including:
    - Database connectivity
    - ML model availability
    - Document count
    """
    # Determine overall status
    if app_state["database_connected"] and app_state["model_loaded"]:
        status = "healthy"
    elif app_state["database_connected"] or app_state["model_loaded"]:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        version="1.0.0",
        database_connected=app_state["database_connected"],
        model_loaded=app_state["model_loaded"],
        document_count=app_state["document_count"],
        timestamp=datetime.utcnow()
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - provides API information and links.
    """
    return {
        "name": "HalalBot API",
        "version": "1.0.0",
        "description": "Islamic Knowledge Assistant REST API",
        "endpoints": {
            "chat": "/api/chat (POST)",
            "search": "/api/search (POST)",
            "health": "/api/health (GET)",
            "docs": "/api/docs (Swagger UI)",
            "redoc": "/api/redoc (ReDoc)"
        },
        "web_app": "https://halalbot2-production.up.railway.app",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api", tags=["root"])
async def api_root():
    """
    API root - same as root but under /api path.
    """
    return await root()


# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Railway sets this) or default to 8000
    port = int(os.environ.get("API_PORT", 8000))
    
    print(f"🕌 Starting HalalBot API on port {port}...")
    print(f"📖 API docs available at: http://localhost:{port}/api/docs")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes (dev only)
    )