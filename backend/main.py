from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# === CONNECTION MANAGER ===
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def register(self, websocket: WebSocket, username: str):
        self.active_connections[websocket] = username
        await self.broadcast_users()


manager = ConnectionManager()

@app.get("/")
async def home():
    with open("../frontend/index.html") as f:
        return HTMLResponse(f.read())
    
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        username = await ws.receive_text()
        await manager.register(ws, username)

    except WebSocketDisconnect:
        manager.disconnect(ws)