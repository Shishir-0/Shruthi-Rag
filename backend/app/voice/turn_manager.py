"""
SHRUTI Turn & Barge-In Manager
Manages turn IDs, session IDs, speculative retrieval tasks, barge-in signals, and instant turn cancellation.
"""
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class TurnManager:
    def __init__(self):
        self.active_turns: Dict[str, str] = {} # session_id -> active_turn_id
        self.conversations: Dict[str, str] = {} # session_id -> conversation_id
        self.running_tasks: Dict[str, List[asyncio.Task]] = {} # turn_id -> list of tasks

    def get_or_create_session(self, explicit_session_id: Optional[str] = None) -> tuple[str, str]:
        session_id = explicit_session_id or f"sess_{uuid.uuid4().hex[:12]}"
        if session_id not in self.conversations:
            self.conversations[session_id] = f"conv_{uuid.uuid4().hex[:12]}"
        return session_id, self.conversations[session_id]

    def start_new_turn(self, session_id: str) -> str:
        """Starts a new conversation turn and cancels any active previous turn (Barge-In)."""
        if session_id in self.active_turns:
            old_turn_id = self.active_turns[session_id]
            self.cancel_turn(old_turn_id, reason="New user turn started / Barge-in")

        new_turn_id = f"turn_{uuid.uuid4().hex[:12]}"
        self.active_turns[session_id] = new_turn_id
        self.running_tasks[new_turn_id] = []
        logger.info(f"Started new turn {new_turn_id} for session {session_id}")
        return new_turn_id

    def register_task(self, turn_id: str, task: asyncio.Task):
        """Registers an asynchronous task (retrieval, LLM, TTS) to a turn."""
        if turn_id in self.running_tasks:
            self.running_tasks[turn_id].append(task)

    def cancel_turn(self, turn_id: str, reason: str = "Barge-in"):
        """Cancels all active tasks associated with the specified turn."""
        if turn_id in self.running_tasks:
            tasks = self.running_tasks.pop(turn_id)
            for t in tasks:
                if not t.done():
                    t.cancel()
            logger.info(f"Cancelled {len(tasks)} tasks for turn {turn_id}. Reason: {reason}")

    def is_turn_active(self, session_id: str, turn_id: str) -> bool:
        """Verifies if the specified turn is still active."""
        return self.active_turns.get(session_id) == turn_id

    def cleanup_session(self, session_id: str):
        if session_id in self.active_turns:
            turn_id = self.active_turns.pop(session_id)
            self.cancel_turn(turn_id, reason="Session closed")
        self.conversations.pop(session_id, None)

turn_manager = TurnManager()
