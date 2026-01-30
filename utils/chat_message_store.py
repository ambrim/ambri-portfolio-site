from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Literal
import json
from clients.redis_client import redis_client

Role = Literal["user", "agent"]


@dataclass
class ChatMessage:
    role: Role
    content: str
    timestamp: str
    
    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @staticmethod
    def from_dict(data):
        return ChatMessage(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"]
        )


class ChatStore:
    def __init__(self, session_id: str, max_size: int = 100):
        self.session_id = session_id
        self.max_size = max_size
        self.key = f"chat:{session_id}"
        self.ttl = 86400  # 24 hours

    def add(self, role: str, content: str) -> None:
        entry = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        # Add to Redis list
        redis_client.lpush(self.key, json.dumps(entry.to_dict()))
        
        # Trim to max size
        redis_client.ltrim(self.key, 0, self.max_size - 1)
        
        # Reset expiration
        redis_client.expire(self.key, self.ttl)

    def all(self) -> List[ChatMessage]:
        """Get all messages as ChatMessage objects (newest first in Redis)"""
        messages_json = redis_client.lrange(self.key, 0, -1)
        messages = [ChatMessage.from_dict(json.loads(msg)) for msg in messages_json]
        # Reverse to get oldest first (matching original behavior)
        messages.reverse()
        return messages

    def clear(self) -> None:
        redis_client.delete(self.key)

    def __len__(self) -> int:
        return redis_client.llen(self.key)
    
    def format_messages(self) -> List[Dict]:
        entries = []
        
        for idx, entry in enumerate(self.all()):
            entries.append({
                "id": idx,
                "role": entry.role,
                "content": entry.content,
                "timestamp": entry.timestamp
            })
        
        return entries