from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # Store active connections by group_id -> {user_id: websocket}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}
        # Store user typing status by group_id -> {user_id: is_typing}
        self.typing_users: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, group_id: int, user_id: int):
        """Accept WebSocket connection and add to group"""
        await websocket.accept()
        
        if group_id not in self.active_connections:
            self.active_connections[group_id] = {}
        
        self.active_connections[group_id][user_id] = websocket
        
        # Initialize typing status for group if needed
        if group_id not in self.typing_users:
            self.typing_users[group_id] = set()
        
        # Notify group that user joined
        await self.broadcast_to_group(group_id, {
            "type": "user_joined",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_user=user_id)

    def disconnect(self, group_id: int, user_id: int):
        """Remove connection from group"""
        if group_id in self.active_connections:
            if user_id in self.active_connections[group_id]:
                del self.active_connections[group_id][user_id]
            
            # Remove from typing users
            self.typing_users[group_id].discard(user_id)
            
            # Clean up empty groups
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
                if group_id in self.typing_users:
                    del self.typing_users[group_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific websocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            # Connection might be closed
            pass

    async def broadcast_to_group(self, group_id: int, message: dict, exclude_user: int = None):
        """Send message to all users in a group"""
        if group_id not in self.active_connections:
            return
        
        disconnected_users = []
        for user_id, websocket in self.active_connections[group_id].items():
            if exclude_user and user_id == exclude_user:
                continue
            
            try:
                await websocket.send_text(json.dumps(message))
            except:
                # Mark for removal if connection is dead
                disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(group_id, user_id)

    async def handle_typing(self, group_id: int, user_id: int, is_typing: bool):
        """Handle typing indicators"""
        if group_id not in self.typing_users:
            self.typing_users[group_id] = set()
        
        if is_typing:
            self.typing_users[group_id].add(user_id)
        else:
            self.typing_users[group_id].discard(user_id)
        
        # Broadcast typing status to group
        await self.broadcast_to_group(group_id, {
            "type": "typing_update",
            "typing_users": list(self.typing_users[group_id]),
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_message_to_group(self, group_id: int, message_data: dict):
        """Send a new message to all group members"""
        await self.broadcast_to_group(group_id, {
            "type": "new_message",
            "message": message_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to specific websocket"""
        await self.send_personal_message({
            "type": "error",
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def get_online_users(self, group_id: int) -> List[int]:
        """Get list of online user IDs for a group"""
        if group_id in self.active_connections:
            return list(self.active_connections[group_id].keys())
        return []

    def is_user_online(self, group_id: int, user_id: int) -> bool:
        """Check if a specific user is online in a group"""
        return (group_id in self.active_connections and 
                user_id in self.active_connections[group_id])

# Global connection manager instance
manager = ConnectionManager()
