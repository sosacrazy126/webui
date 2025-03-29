#!/usr/bin/env python3
import argparse
import asyncio
import json
import shutil
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Verify ra-aid is available
if not shutil.which("ra-aid"):
    print(
        "Error: ra-aid command not found. Please ensure it's installed and in your PATH"
    )
    sys.exit(1)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory=Path(__file__).parent)


# Create a route for the root to serve index.html with port parameter
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    """Serve the index.html file with port parameter."""
    # Default to enhanced server port (8000)
    enhanced_server_port = 8000
    return templates.TemplateResponse(
        "index.html", {"request": request, "server_port": enhanced_server_port}
    )


# Mount static files for js and other assets
app.mount("/static", StaticFiles(directory=Path(__file__).parent), name="static")

# Store active proxy connections
proxy_connections: Dict[str, WebSocket] = {}
enhanced_connections: Dict[str, websockets.WebSocketClientProtocol] = {}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint that proxies connections to the enhanced server.
    
    Args:
        websocket: WebSocket connection from client
        client_id: Client identifier
    """
    await websocket.accept()
    print(f"WebSocket connection accepted for client {client_id}")
    
    # Store client connection
    proxy_connections[client_id] = websocket
    
    try:
        # Connect to enhanced server
        enhanced_server_url = f"ws://localhost:8000/ws/{client_id}"
        print(f"Connecting to enhanced server at {enhanced_server_url}")
        
        async with websockets.connect(enhanced_server_url) as enhanced_ws:
            enhanced_connections[client_id] = enhanced_ws
            
            # Create tasks for bidirectional communication
            client_to_server_task = asyncio.create_task(
                forward_messages(websocket, enhanced_ws, client_id, "client -> server")
            )
            server_to_client_task = asyncio.create_task(
                forward_messages(enhanced_ws, websocket, client_id, "server -> client")
            )
            
            # Wait for either task to complete (usually due to disconnection)
            done, pending = await asyncio.wait(
                [client_to_server_task, server_to_client_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel the pending task
            for task in pending:
                task.cancel()
    
    except Exception as e:
        print(f"Error in WebSocket proxy for client {client_id}: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Proxy error: {str(e)}"
            })
        except:
            pass
    
    finally:
        # Clean up connections
        proxy_connections.pop(client_id, None)
        enhanced_connections.pop(client_id, None)
        print(f"WebSocket proxy connection cleaned up for client {client_id}")


async def forward_messages(source: WebSocket, destination: WebSocket, client_id: str, direction: str):
    """
    Forward messages between WebSocket connections.
    
    Args:
        source: Source WebSocket
        destination: Destination WebSocket
        client_id: Client identifier
        direction: Direction of message flow (for logging)
    """
    try:
        while True:
            # Receive message from source
            message = await source.receive_text()
            print(f"[{direction}] Forwarding message for client {client_id}")
            
            # Forward to destination
            if isinstance(destination, WebSocket):
                await destination.send_text(message)
            else:
                await destination.send(message)
    
    except Exception as e:
        print(f"Error forwarding messages for client {client_id} [{direction}]: {str(e)}")
        raise


@app.get("/config")
async def get_config(request: Request):
    """Return server configuration including host and port."""
    return {"host": request.client.host, "port": request.scope.get("server")[1]}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Check if we can connect to the enhanced server
    try:
        async with websockets.connect("ws://localhost:8000/health") as ws:
            await ws.send(json.dumps({"type": "ping"}))
            result = await asyncio.wait_for(ws.recv(), timeout=5)
            return {"status": "healthy", "enhanced_server": json.loads(result)}
    except:
        return {"status": "degraded", "enhanced_server": "unavailable"}


def run_server(host: str = "0.0.0.0", port: int = 3000):
    """Run the proxy server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RA.Aid Web Interface Proxy Server")
    parser.add_argument(
        "--port", type=int, default=3000, help="Port to listen on (default: 3000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to listen on (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--enhanced-port",
        type=int, 
        default=8000,
        help="Port of the enhanced server (default: 8000)"
    )

    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
