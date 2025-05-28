import asyncio
import json
import time
from datetime import datetime
from typing import Union, List, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI()

# WebSocket connection manager for chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove stale connections
                    self.active_connections[room_id].remove(connection)

manager = ConnectionManager()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/demo", response_class=HTMLResponse)
async def get_demo():
    """
    Serve the SSE demo HTML page
    """
    try:
        with open("sse_demo.html", "r") as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Demo file not found</h1><p>Please make sure sse_demo.html exists in the project directory.</p>")

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}

# WebSocket endpoints

@app.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time chat functionality
    """
    await manager.connect(websocket, room_id)
    
    # Send welcome message
    welcome_message = {
        "type": "system",
        "message": f"Connected to room {room_id}",
        "timestamp": datetime.now().isoformat(),
        "room_id": room_id
    }
    await manager.send_personal_message(json.dumps(welcome_message), websocket)
    
    # Notify room about new user
    join_message = {
        "type": "user_joined",
        "message": "A user joined the room",
        "timestamp": datetime.now().isoformat(),
        "room_id": room_id,
        "user_count": len(manager.active_connections.get(room_id, []))
    }
    await manager.broadcast_to_room(json.dumps(join_message), room_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Add server-side metadata
            response_message = {
                "type": "chat_message",
                "user": message_data.get("user", "Anonymous"),
                "message": message_data.get("message", ""),
                "timestamp": datetime.now().isoformat(),
                "room_id": room_id,
                "id": int(time.time() * 1000)
            }
            
            # Broadcast message to all clients in the room
            await manager.broadcast_to_room(json.dumps(response_message), room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        
        # Notify room about user leaving
        leave_message = {
            "type": "user_left",
            "message": "A user left the room",
            "timestamp": datetime.now().isoformat(),
            "room_id": room_id,
            "user_count": len(manager.active_connections.get(room_id, []))
        }
        await manager.broadcast_to_room(json.dumps(leave_message), room_id)

@app.websocket("/ws/echo")
async def websocket_echo_endpoint(websocket: WebSocket):
    """
    Simple WebSocket echo endpoint for testing
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            echo_message = {
                "type": "echo",
                "original": data,
                "timestamp": datetime.now().isoformat(),
                "message": f"Echo: {data}"
            }
            await websocket.send_text(json.dumps(echo_message))
    except WebSocketDisconnect:
        print("WebSocket echo client disconnected")

# Server-Sent Events endpoints

@app.get("/events/stream")
async def stream_events():
    """
    Basic SSE endpoint that sends periodic updates
    """
    async def event_generator():
        counter = 0
        while True:
            # Check if client is still connected
            try:
                counter += 1
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Server time update #{counter}",
                    "counter": counter
                }
                
                # SSE format: data: {json}\n\n
                yield f"data: {json.dumps(data)}\n\n"
                
                # Wait 2 seconds before next event
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Client disconnected: {e}")
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/events/notifications")
async def notification_stream():
    """
    SSE endpoint for notifications with different event types
    """
    async def notification_generator():
        notifications = [
            {"type": "info", "message": "System started successfully"},
            {"type": "warning", "message": "High memory usage detected"},
            {"type": "success", "message": "Backup completed"},
            {"type": "error", "message": "Connection timeout"},
            {"type": "info", "message": "New user registered"}
        ]
        
        for i, notification in enumerate(notifications):
            data = {
                "id": i + 1,
                "timestamp": datetime.now().isoformat(),
                **notification
            }
            
            # SSE with event type
            yield f"event: notification\n"
            yield f"data: {json.dumps(data)}\n\n"
            
            await asyncio.sleep(3)
    
    return StreamingResponse(
        notification_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/events/data-feed")
async def data_feed_stream():
    """
    SSE endpoint that simulates real-time data feed (like stock prices, sensor data, etc.)
    """
    async def data_generator():
        import random
        
        base_price = 100.0
        
        while True:
            try:
                # Simulate price fluctuation
                change = random.uniform(-2.0, 2.0)
                base_price += change
                
                data = {
                    "symbol": "DEMO",
                    "price": round(base_price, 2),
                    "change": round(change, 2),
                    "timestamp": datetime.now().isoformat(),
                    "volume": random.randint(1000, 50000)
                }
                
                yield f"event: price-update\n"
                yield f"data: {json.dumps(data)}\n\n"
                
                # Random interval between 0.5 and 2 seconds
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                print(f"Data feed error: {e}")
                break
    
    return StreamingResponse(
        data_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@app.get("/events/chat/{room_id}")
async def chat_stream(room_id: str):
    """
    SSE endpoint for chat-like functionality (read-only)
    You could extend this to work with a real message queue/database
    """
    async def chat_generator():
        # Simulated chat messages for demonstration
        messages = [
            {"user": "Alice", "message": f"Joined room {room_id}"},
            {"user": "Bob", "message": "Hello everyone!"},
            {"user": "Alice", "message": "How's everyone doing?"},
            {"user": "Charlie", "message": "Great to be here!"},
            {"user": "Bob", "message": "Let's discuss the project"},
        ]
        
        for msg in messages:
            data = {
                "room_id": room_id,
                "timestamp": datetime.now().isoformat(),
                "id": int(time.time() * 1000),  # Simple ID generation
                **msg
            }
            
            yield f"event: message\n"
            yield f"data: {json.dumps(data)}\n\n"
            
            await asyncio.sleep(4)  # 4 seconds between messages
    
    return StreamingResponse(
        chat_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
