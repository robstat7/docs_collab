from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()

# === CONNECTION MANAGER ===
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        print("@@@ws accepted!")

    def disconnect(self, websocket: WebSocket):
        username = self.active_connections.pop(websocket, None)
        return username

    async def register(self, websocket: WebSocket, username: str):
        self.active_connections[websocket] = username

    # avoid sending updates back to the originator
    async def broadcast(self, message: str, ws: WebSocket):
        for conn in self.active_connections:
            if conn != ws:
                await conn.send_text(message)

    # broadcast system notifications to all clients
    async def broadcast_system_message(self, message: str):
        for conn in self.active_connections:
            await conn.send_text(json.dumps({
                "type": "system",
                "message": message
            }))


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

        # notify all users about new join
        await manager.broadcast_system_message(f"{username} joined the document")

        while True:
            data = await ws.receive_text()
            await manager.broadcast(data, ws)

    except WebSocketDisconnect:
        username = manager.disconnect(ws)
        if username:
            # Notify all users about leave
            await manager.broadcast_system_message(f"{username} left the document")