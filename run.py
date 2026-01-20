#!/usr/bin/env python3
"""
HalalBot Combined Server Runner
v7 - Fixed WebSocket message handling
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

from api.schemas import HealthResponse
from api.routes.chat import router as chat_router

# ============================================================================
# CONFIGURATION
# ============================================================================

MAIN_PORT = int(os.environ.get("PORT", 8080))
STREAMLIT_PORT = 8501
STREAMLIT_HTTP_URL = f"http://127.0.0.1:{STREAMLIT_PORT}"

streamlit_process = None
http_client = None
aiohttp_session = None


# ============================================================================
# STREAMLIT SUBPROCESS
# ============================================================================

def start_streamlit():
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
    
    def log_output():
        try:
            for line in streamlit_process.stdout:
                print(f"[Streamlit] {line.rstrip()}")
        except:
            pass
    
    threading.Thread(target=log_output, daemon=True).start()
    
    print("⏳ Waiting for Streamlit...")
    for i in range(60):
        try:
            with httpx.Client(timeout=2.0) as client:
                if client.get(f"{STREAMLIT_HTTP_URL}/_stcore/health").status_code == 200:
                    print(f"✅ Streamlit ready on port {STREAMLIT_PORT}")
                    time.sleep(1)
                    return True
        except:
            pass
        time.sleep(1)
    
    print("⚠️  Streamlit may not be ready")
    return False


def stop_streamlit():
    global streamlit_process
    if streamlit_process:
        print("🛑 Stopping Streamlit...")
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=5)
        except:
            streamlit_process.kill()
        streamlit_process = None


def signal_handler(signum, frame):
    print(f"\n📴 Signal {signum}, shutting down...")
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
}


# ============================================================================
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, aiohttp_session
    
    print("🚀 HalalBot starting...")
    print(f"📡 Port: {MAIN_PORT}")
    
    start_streamlit()
    
    http_client = httpx.AsyncClient(base_url=STREAMLIT_HTTP_URL, timeout=30.0, follow_redirects=True)
    aiohttp_session = aiohttp.ClientSession()
    print("✅ HTTP proxy initialized")
    
    try:
        from config.database import get_db_manager
        db = get_db_manager()
        if db.health_check():
            app_state["database_connected"] = True
            result = db.execute_query("SELECT COUNT(*) as count FROM documents", fetch=True, fetch_one=True)
            if result:
                app_state["document_count"] = result.get('count', 0)
            print(f"✅ Database: {app_state['document_count']:,} documents")
    except Exception as e:
        print(f"⚠️  Database: {e}")
    
    try:
        from sentence_transformers import SentenceTransformer
        app_state["model_loaded"] = True
        print("✅ Model available")
    except Exception as e:
        print(f"⚠️  Model: {e}")
    
    print("🕌 HalalBot ready!")
    print(f"   • Web: http://localhost:{MAIN_PORT}/")
    print(f"   • API: http://localhost:{MAIN_PORT}/api/docs")
    
    yield
    
    print("👋 Shutting down...")
    if http_client:
        await http_client.aclose()
    if aiohttp_session:
        await aiohttp_session.close()
    stop_streamlit()


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HalalBot",
    description="Islamic Knowledge Assistant",
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
    status = "healthy" if app_state["database_connected"] and app_state["model_loaded"] else "degraded"
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
    return {"name": "HalalBot API", "version": "1.0.0"}


# ============================================================================
# WEBSOCKET PROXY
# ============================================================================

@app.websocket("/_stcore/stream")
async def websocket_proxy(websocket: WebSocket):
    """Proxy WebSocket to Streamlit"""
    global aiohttp_session
    
    await websocket.accept()
    
    query_string = websocket.scope.get("query_string", b"").decode("utf-8")
    ws_url = f"ws://127.0.0.1:{STREAMLIT_PORT}/_stcore/stream"
    if query_string:
        ws_url += f"?{query_string}"
    
    try:
        async with aiohttp_session.ws_connect(
            ws_url,
            headers={
                "Host": f"127.0.0.1:{STREAMLIT_PORT}",
                "Origin": f"http://127.0.0.1:{STREAMLIT_PORT}",
            },
            compress=0,
            autoclose=False,
            autoping=True,
        ) as streamlit_ws:
            
            print("✅ WebSocket proxy connected")
            
            async def forward_to_streamlit():
                """Browser → Streamlit"""
                try:
                    while True:
                        msg = await websocket.receive()
                        msg_type = msg.get("type", "")
                        
                        if msg_type == "websocket.receive":
                            if "text" in msg:
                                await streamlit_ws.send_str(msg["text"])
                            elif "bytes" in msg:
                                await streamlit_ws.send_bytes(msg["bytes"])
                        elif msg_type == "websocket.disconnect":
                            print("Client disconnected")
                            break
                except WebSocketDisconnect:
                    print("Client WebSocket disconnected")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Client→Streamlit error: {type(e).__name__}: {e}")
            
            async def forward_to_client():
                """Streamlit → Browser"""
                try:
                    while True:
                        msg = await streamlit_ws.receive()
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await websocket.send_text(msg.data)
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            await websocket.send_bytes(msg.data)
                        elif msg.type == aiohttp.WSMsgType.PING:
                            await streamlit_ws.pong(msg.data)
                        elif msg.type == aiohttp.WSMsgType.PONG:
                            pass  # Ignore pongs
                        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED):
                            print("Streamlit closed WebSocket")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"Streamlit WS error: {streamlit_ws.exception()}")
                            break
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    print(f"Streamlit→Client error: {type(e).__name__}: {e}")
            
            # Run both directions
            task1 = asyncio.create_task(forward_to_streamlit())
            task2 = asyncio.create_task(forward_to_client())
            
            done, pending = await asyncio.wait(
                [task1, task2],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining task
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            print("WebSocket proxy session ended")
                
    except aiohttp.WSServerHandshakeError as e:
        print(f"WebSocket handshake failed: {e.status}")
    except Exception as e:
        print(f"WebSocket error: {type(e).__name__}: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============================================================================
# HTTP PROXY
# ============================================================================

async def proxy_http(request: Request, path: str) -> Response:
    global http_client
    if not http_client:
        return Response(content="Proxy not ready", status_code=503)
    
    url = f"/{path}" if path else "/"
    if request.query_params:
        url += f"?{request.query_params}"
    
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in ("host", "connection", "transfer-encoding", "upgrade")}
    headers["Host"] = f"127.0.0.1:{STREAMLIT_PORT}"
    
    try:
        resp = await http_client.request(method=request.method, url=url, headers=headers, content=body)
        resp_headers = {k: v for k, v in resp.headers.items()
                       if k.lower() not in ("transfer-encoding", "connection", "content-encoding")}
        return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers)
    except httpx.ConnectError:
        return Response(content="Streamlit starting...", status_code=503)
    except Exception as e:
        return Response(content=f"Error: {e}", status_code=502)


@app.get("/", include_in_schema=False)
async def root(request: Request):
    return await proxy_http(request, "")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"], include_in_schema=False)
async def catch_all(request: Request, path: str):
    return await proxy_http(request, path)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🕌 HalalBot Combined Server")
    print("=" * 50)
    uvicorn.run("run:app", host="0.0.0.0", port=MAIN_PORT, log_level="info")
