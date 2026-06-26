# app/core/memory.py
"""
Conversation Memory Manager
Stores per-session message history in memory.
In production: replace with Redis or a database.
"""

from collections import defaultdict
from app.core.config import MEMORY_WINDOW


class MemoryManager:
    def __init__(self):
        self._store: dict[str, list[dict]] = defaultdict(list)

    def get_history(self, session_id: str) -> list[dict]:
        """Return the last N messages for a session."""
        return self._store[session_id][-MEMORY_WINDOW:]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append a message to session history."""
        self._store[session_id].append({"role": role, "content": content})

    def clear(self, session_id: str) -> None:
        """Clear history for a session."""
        self._store.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._store)


# Singleton instance used across the app
memory = MemoryManager()
