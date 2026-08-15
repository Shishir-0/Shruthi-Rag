"""
SHRUTI Turn & Barge-In Manager
Manages turn IDs, speculative retrieval tasks, barge-in signals, and turn cancellation.
"""
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TurnManager:
    def __init__(self):
        self.active_turns: Dict[str, str] = {} # session_id -> active_turn_id
        self.running_tasks: Dict[str, asyncio.Task] = {} # turn_id -> task

    def start_new_turn(self, session_id: str) -> str:
        """Starts a new conversation turn and cancels any active previous turn (Barge-In)."""
        if session_id in self.active_turns:
            old_turn_id = self.active_turns[session_id]
            self.cancel_turn(old_turn_id, reason="New user turn started / Barge-in")

        new_turn_id = f"turn_{uuid.uuid4().hex[:10]}"
        self.active_turns[session_id] = new_turn_id
        logger.info(f"Started new turn {new_turn_id} for session {session_id}")
        return new_turn_id

    def cancel_turn(self, turn_id: str, reason: str = "Barge-in"):
        """Cancels active tasks for the specified turn."""
        if turn_id in self.running_tasks:
            task = self.running_tasks.pop(turn_id)
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled task for turn {turn_id}. Reason: {reason}")

    def is_turn_active(self, session_id: str, turn_id: str) -> bool:
        """Verifies if the specified turn is still active."""
        return self.active_turns.get(session_id) == turn_id

turn_manager = TurnManager()
