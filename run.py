#!/usr/bin/env python3
"""
HalalBot Combined Server Runner

Runs both FastAPI (REST API) and Streamlit (Web App) together.
- FastAPI handles /api/* routes for the iOS app
- Streamlit handles all other routes for the web app
- WebSocket connections are properly proxied to Streamlit using aiohttp

Railway runs this script, which starts both services.
"""

import os
import sys
import subprocess
import signal
import time
import threading
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import httpx
import aiohttp

# Import the API routes
from api.schemas import HealthResponse
from api.routes.chat import router as chat_router


# ============================================================================
# CONFIGURATION
# ============================================================================

MAIN_PORT = int(os.environ.get("PORT", 8080))
STREAMLIT_PORT = 8501
STREAMLIT_HTTP_URL = f"http://127.0.0.1:{STREAMLIT_PORT}"
STREAMLIT_WS_URL = f"http://127.0.0.1:{STREAMLIT_PORT}"  # aiohttp uses http:// for ws

streamlit_process = None
http_client = None
aiohttp_session = None  # For WebSocket connections


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
        "--server.address=127.0.0.1",
        "--server.headless=true",
        "--server.runOnSave=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
        # These are critical for WebSocket proxying
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.enableWebsocketCompression=false",
    ]
    
    streamlit_process = subprocess.Popen(
        streamlit_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    def log_streamlit_output():
        try:
            for line in streamlit_process.stdout:
                print(f"[Streamlit] {line.rstrip()}")
        except Exception:
            pass
    
    thread = threading.Thread(target=log_streamlit_output, daemon=True)
    thread.start()
    
    print("⏳ Waiting for Streamlit to be ready...")
    max_retries = 60
    
    for i in range(max_retries):
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{STREAMLIT_HTTP_URL}/_stcore/health")
                if response.status_code == 200:
                    print(f"✅ Streamlit is ready on port {STREAMLIT_PORT}")
                    time.sleep(1)
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
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, aiohttp_session
    
    print("🚀 HalalBot Combined Server starting...")
    print(f"📡 Main port: {MAIN_PORT}")
    
    # Start Streamlit
    app_state["streamlit_running"] = start_streamlit()
    
    # Initialize HTTP clients
    http_client = httpx.AsyncClient(
        base_url=STREAMLIT_HTTP_URL,
        timeout=30.0,
        follow_redirects=True
    )
    
    # Create aiohttp session for WebSocket proxying
    aiohttp_session = aiohttp.ClientSession()
    
    print("✅ HTTP proxy client initialized")
    
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
            print(f"✅ Database connected - {app_state['document_count']:,} documents available")
        else:
            print("⚠️  Database health check failed")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
    
    # Test model
    try:
        from sentence_transformers import SentenceTransformer
        app_state["model_loaded"] = True
        print("✅ Sentence transformer model available")
    except Exception as e:
        print(f"⚠️  Model loading failed: {e}")
    
    print("🕌 HalalBot is ready!")
    print(f"   • Web App: http://localhost:{MAIN_PORT}/")
    print(f"   • API Docs: http://localhost:{MAIN_PORT}/api/docs")
    
    yield
    
    # Shutdown
    print("👋 Shutting down HalalBot...")
    if http_client:
        await http_client.aclose()
    if aiohttp_session:
        await aiohttp_session.close()
    stop_streamlit()
    
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
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
# WEBSOCKET PROXY TO STREAMLIT (using aiohttp)
# ============================================================================

@app.websocket("/_stcore/stream")
async def websocket_proxy(websocket: WebSocket):
    """
    Proxy WebSocket connections to Streamlit using aiohttp.
    """
    global aiohttp_session
    
    await websocket.accept()
    
    # Build the Streamlit WebSocket URL
    query_string = websocket.scope.get("query_string", b"").decode("utf-8")
    ws_url = f"ws://127.0.0.1:{STREAMLIT_PORT}/_stcore/stream"
    if query_string:
        ws_url += f"?{query_string}"
    
    streamlit_ws = None
    
    try:
        # Connect to Streamlit using aiohttp
        streamlit_ws = await aiohttp_session.ws_connect(
            ws_url,
            headers={
                "Host": f"127.0.0.1:{STREAMLIT_PORT}",
                "Origin": f"http://127.0.0.1:{STREAMLIT_PORT}",
            },
            compress=0,  # Disable compression to match Streamlit setting
        )
        
        print(f"✅ WebSocket connected to Streamlit")
        
        async def client_to_streamlit():
            """Forward messages from browser to Streamlit"""
            try:
                while True:
                    data = await websocket.receive()
                    if data["type"] == "websocket.receive":
                        if "text" in data:
                            await streamlit_ws.send_str(data["text"])
                        elif "bytes" in data:
                            await streamlit_ws.send_bytes(data["bytes"])
                    elif data["type"] == "websocket.disconnect":
                        break
            except WebSocketDisconnect:
                pass
            except Exception as e:
                if "disconnect" not in str(e).lower():
                    print(f"Client→Streamlit error: {type(e).__name__}: {e}")
        
        async def streamlit_to_client():
            """Forward messages from Streamlit to browser"""
            try:
                async for msg in streamlit_ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await websocket.send_text(msg.data)
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        await websocket.send_bytes(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"Streamlit WS error: {streamlit_ws.exception()}")
                        break
            except Exception as e:
                if "disconnect" not in str(e).lower():
                    print(f"Streamlit→Client error: {type(e).__name__}: {e}")
        
        # Run both directions concurrently
        client_task = asyncio.create_task(client_to_streamlit())
        streamlit_task = asyncio.create_task(streamlit_to_client())
        
        done, pending = await asyncio.wait(
            [client_task, streamlit_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
                
    except aiohttp.WSServerHandshakeError as e:
        print(f"WebSocket handshake failed: {e.status} - {e.message}")
    except Exception as e:
        print(f"WebSocket proxy error: {type(e).__name__}: {e}")
    finally:
        if streamlit_ws and not streamlit_ws.closed:
            await streamlit_ws.close()
        try:
            await websocket.close()
        except Exception:
            pass


# ============================================================================
# HTTP PROXY TO STREAMLIT
# ============================================================================

async def proxy_http_request(request: Request, path: str) -> Response:
    global http_client
    
    if http_client is None:
        return Response(content="Proxy not initialized.", status_code=503)
    
    url = f"/{path}" if path else "/"
    if request.query_params:
        url += f"?{request.query_params}"
    
    body = await request.body()
    
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ("host", "connection", "transfer-encoding", "upgrade"):
            headers[key] = value
    headers["Host"] = f"127.0.0.1:{STREAMLIT_PORT}"
    
    try:
        response = await http_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
        )
        
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                response_headers[key] = value
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
        )
    except httpx.ConnectError:
        return Response(content="Streamlit starting...", status_code=503)
    except Exception as e:
        return Response(content=f"Proxy error: {e}", status_code=502)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return await proxy_http_request(request, "")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"], include_in_schema=False)
async def proxy_to_streamlit(request: Request, path: str):
    return await proxy_http_request(request, path)


# ============================================================================
# MAIN
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
