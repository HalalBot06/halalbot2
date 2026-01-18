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
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response
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
STREAMLIT_URL = f"http://127.0.0.1:{STREAMLIT_PORT}"

# Global reference to Streamlit process
streamlit_process = None

# Global HTTP client for proxying (initialized in lifespan)
http_client = None


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
        try:
            for line in streamlit_process.stdout:
                print(f"[Streamlit] {line.rstrip()}")
        except Exception:
            pass
    
    thread = threading.Thread(target=log_streamlit_output, daemon=True)
    thread.start()
    
    # Wait for Streamlit to be ready (with longer timeout)
    print("⏳ Waiting for Streamlit to be ready...")
    max_retries = 60  # Increased from 30
    
    for i in range(max_retries):
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{STREAMLIT_URL}/_stcore/health")
                if response.status_code == 200:
                    print(f"✅ Streamlit is ready on port {STREAMLIT_PORT}")
                    # Give it a bit more time to fully initialize
                    time.sleep(2)
                    return True
        except Exception:
            pass
        time.sleep(1)
        if i > 0 and i % 10 == 0:
            print(f"   Still waiting for Streamlit... ({i}s)")
    
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
# GLOBAL STATE
# ============================================================================

app_state = {
    "database_connected": False,
    "model_loaded": False,
    "document_count": None,
    "streamlit_running": False
}


# ============================================================================
# LIFESPAN (ALL STARTUP/SHUTDOWN IN ONE PLACE)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global http_client
    
    # === STARTUP ===
    print("🚀 HalalBot Combined Server starting...")
    print(f"📡 Main port: {MAIN_PORT}")
    
    # Start Streamlit FIRST
    app_state["streamlit_running"] = start_streamlit()
    
    # Initialize HTTP client for proxying AFTER Streamlit is ready
    http_client = httpx.AsyncClient(
        base_url=STREAMLIT_URL,
        timeout=30.0,
        follow_redirects=True
    )
    print("✅ HTTP proxy client initialized")
    
    # Test database connection using DatabaseManager
    try:
        from config.database import get_db_manager
        db = get_db_manager()
        
        if db.health_check():
            app_state["database_connected"] = True
            
            result = db.execute_query(
                "SELECT COUNT(*) as count FROM documents",
                fetch=True,
                fetch_one=True
            )
            if result:
                app_state["document_count"] = result.get('count', 0)
            
            print(f"✅ Database connected - {app_state['document_count']:,} documents available")
        else:
            print("⚠️  Database health check failed")
            
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        app_state["database_connected"] = False
    
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
    
    yield  # ===== APP RUNS HERE =====
    
    # === SHUTDOWN ===
    print("👋 Shutting down HalalBot...")
    
    # Close HTTP client
    if http_client:
        await http_client.aclose()
    
    # Stop Streamlit
    stop_streamlit()
    
    # Cleanup database connections
    try:
        from config.database import cleanup_database
        cleanup_database()
    except Exception:
        pass


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

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

async def proxy_request(request: Request, path: str) -> Response:
    """
    Proxy a request to Streamlit.
    """
    global http_client
    
    if http_client is None:
        return Response(
            content="Proxy not initialized. Please wait...",
            status_code=503,
            media_type="text/plain"
        )
    
    # Build the target URL
    url = f"/{path}" if path else "/"
    if request.query_params:
        url += f"?{request.query_params}"
    
    # Get request body if present
    body = await request.body()
    
    # Forward headers (excluding hop-by-hop headers)
    headers = {}
    for key, value in request.headers.items():
        key_lower = key.lower()
        if key_lower not in ("host", "connection", "transfer-encoding", "upgrade"):
            headers[key] = value
    
    try:
        # Make the proxied request
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        # Build response headers (excluding hop-by-hop)
        response_headers = {}
        for key, value in response.headers.items():
            key_lower = key.lower()
            if key_lower not in ("transfer-encoding", "connection", "content-encoding"):
                response_headers[key] = value
        
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
        print(f"Proxy error: {e}")
        return Response(
            content=f"Proxy error: {str(e)}",
            status_code=502,
            media_type="text/plain"
        )


# Root path - proxy to Streamlit
@app.get("/", include_in_schema=False)
async def root(request: Request):
    """Proxy root to Streamlit"""
    return await proxy_request(request, "")


# Catch-all route - proxy everything else to Streamlit
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"], include_in_schema=False)
async def proxy_to_streamlit(request: Request, path: str):
    """
    Proxy all non-API requests to Streamlit.
    This makes the web app accessible at the root URL.
    """
    return await proxy_request(request, path)


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
