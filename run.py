#!/usr/bin/env python3
"""
HalalBot Combined Server Runner

Runs both FastAPI (REST API) and Streamlit (Web App) together.
- FastAPI handles /api/* routes for the iOS app
- Streamlit handles all other routes for the web app

Railway runs this script, which starts both services.
"""

import os
import sys
import subprocess
import signal
import time
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Import the API routes
from api.schemas import HealthResponse
from api.routes.chat import router as chat_router


# ============================================================================
# CONFIGURATION
# ============================================================================

# Railway provides PORT, we use it for FastAPI (the main entry point)
MAIN_PORT = int(os.environ.get("PORT", 8080))

# Streamlit runs internally on a different port
STREAMLIT_PORT = 8501
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"

# Global reference to Streamlit process
streamlit_process = None


# ============================================================================
# STREAMLIT SUBPROCESS MANAGEMENT
# ============================================================================

def start_streamlit():
    """Start Streamlit as a subprocess"""
    global streamlit_process
    
    print(f"🌐 Starting Streamlit on internal port {STREAMLIT_PORT}...")
    
    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        f"--server.port={STREAMLIT_PORT}",
        "--server.address=127.0.0.1",  # Only accessible internally
        "--server.headless=true",
        "--server.runOnSave=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ]
    
    streamlit_process = subprocess.Popen(
        streamlit_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Log Streamlit output in background thread
    def log_streamlit_output():
        for line in streamlit_process.stdout:
            print(f"[Streamlit] {line.rstrip()}")
    
    thread = threading.Thread(target=log_streamlit_output, daemon=True)
    thread.start()
    
    # Wait for Streamlit to be ready
    print("⏳ Waiting for Streamlit to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            with httpx.Client() as client:
                response = client.get(f"{STREAMLIT_URL}/_stcore/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Streamlit is ready on port {STREAMLIT_PORT}")
                    return True
        except Exception:
            pass
        time.sleep(1)
    
    print("⚠️  Streamlit may not be fully ready, continuing anyway...")
    return False


def stop_streamlit():
    """Stop the Streamlit subprocess"""
    global streamlit_process
    if streamlit_process:
        print("🛑 Stopping Streamlit...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()
        streamlit_process = None


# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n📴 Received signal {signum}, shutting down...")
    stop_streamlit()
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# ============================================================================
# FASTAPI APPLICATION WITH PROXY
# ============================================================================

# Global state for health checks
app_state = {
    "database_connected": False,
    "model_loaded": False,
    "document_count": None,
    "streamlit_running": False
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    
    # === STARTUP ===
    print("🚀 HalalBot Combined Server starting...")
    print(f"📡 Main port: {MAIN_PORT}")
    
    # Start Streamlit
    app_state["streamlit_running"] = start_streamlit()
    
    # Test database connection
    try:
        from config.database import get_db_connection
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            app_state["document_count"] = count
            app_state["database_connected"] = True
            cursor.close()
            conn.close()
            print(f"✅ Database connected - {count:,} documents available")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
    
    # Test model loading
    try:
        from sentence_transformers import SentenceTransformer
        app_state["model_loaded"] = True
        print("✅ Sentence transformer model available")
    except Exception as e:
        print(f"⚠️  Model loading failed: {e}")
    
    print("🕌 HalalBot is ready!")
    print(f"   • Web App: http://localhost:{MAIN_PORT}/")
    print(f"   • API Docs: http://localhost:{MAIN_PORT}/api/docs")
    
    yield  # App runs here
    
    # === SHUTDOWN ===
    print("👋 Shutting down HalalBot...")
    stop_streamlit()


# Create the FastAPI app
app = FastAPI(
    title="HalalBot",
    description="Islamic Knowledge Assistant - Web App & REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # iOS app needs this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat_router)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    
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


@app.get("/api", tags=["api"])
async def api_root():
    """API information"""
    return {
        "name": "HalalBot API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "search": "POST /api/search",
            "health": "GET /api/health",
            "docs": "GET /api/docs"
        }
    }


# ============================================================================
# PROXY TO STREAMLIT (for all non-API routes)
# ============================================================================

# HTTP client for proxying to Streamlit
http_client = None


@app.on_event("startup")
async def startup_http_client():
    global http_client
    http_client = httpx.AsyncClient(base_url=STREAMLIT_URL, timeout=30.0)


@app.on_event("shutdown")
async def shutdown_http_client():
    global http_client
    if http_client:
        await http_client.aclose()


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def proxy_to_streamlit(request: Request, path: str):
    """
    Proxy all non-API requests to Streamlit.
    This makes the web app accessible at the root URL.
    """
    # Build the target URL
    url = f"/{path}"
    if request.query_params:
        url += f"?{request.query_params}"
    
    # Get request body if present
    body = await request.body()
    
    # Forward headers (excluding hop-by-hop headers)
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("connection", None)
    headers.pop("transfer-encoding", None)
    
    try:
        # Make the proxied request
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        # Build response headers (excluding hop-by-hop)
        response_headers = dict(response.headers)
        response_headers.pop("transfer-encoding", None)
        response_headers.pop("connection", None)
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )
        
    except httpx.ConnectError:
        return Response(
            content="Streamlit is starting up, please refresh in a moment...",
            status_code=503,
            media_type="text/plain"
        )
    except Exception as e:
        return Response(
            content=f"Proxy error: {str(e)}",
            status_code=502,
            media_type="text/plain"
        )


# Root path handler (must be after the catch-all route is defined)
@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Proxy root to Streamlit"""
    return await proxy_to_streamlit(request, "")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🕌 HalalBot Combined Server")
    print("=" * 60)
    print(f"Starting on port {MAIN_PORT}...")
    print()
    
    uvicorn.run(
        "run:app",
        host="0.0.0.0",
        port=MAIN_PORT,
        log_level="info",
        access_log=True
    )