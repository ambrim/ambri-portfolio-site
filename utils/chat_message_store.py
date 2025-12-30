from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
import os

Role = Literal["user", "agent"]


@dataclass
class ChatMessage:
    role: Role
    content: str
    timestamp: str


class ChatStore:
    def __init__(self, max_size: int = 100):
        self._messages: deque[ChatMessage] = deque(maxlen=max_size)

    def add(self, role: str, content: str) -> None:
        entry = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._messages.append(entry)

    def all(self) -> List[ChatMessage]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
    
    def format_messages(self) -> List[Dict]:
        entries = []

        for idx, entry in enumerate(self._messages):
          entries.append({
              "id": idx,
              "role": entry.role,
              "content": entry.content,
              "timestamp": entry.timestamp
          })

        return entries

# Singleton instance (shared everywhere) with initial message
chat_store = ChatStore(
    max_size=int(os.getenv("MAX_CHAT_MESSAGES", 100))
)
chat_store.add(
    "agent", 
    "Welcome to my portfolio! 👋 Ask me about projects, experience, or whatever you're curious about."
)