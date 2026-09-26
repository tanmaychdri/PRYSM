"""
Persistent conversation history store.
Saves every message exchange to disk as JSON so sessions are never lost.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from prysm.models.interactions import LLMMessage, LLMToolCall

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "conversation_history.json"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _msg_to_dict(msg: LLMMessage) -> dict:
    d: dict = {"role": msg.role, "content": msg.content}
    if msg.tool_calls:
        d["tool_calls"] = [
            {"call_id": tc.call_id, "tool_name": tc.tool_name, "arguments": tc.arguments}
            for tc in msg.tool_calls
        ]
    if msg.tool_call_id:
        d["tool_call_id"] = msg.tool_call_id
    return d


def _dict_to_msg(d: dict) -> LLMMessage:
    tool_calls = None
    if d.get("tool_calls"):
        tool_calls = [
            LLMToolCall(
                call_id=tc["call_id"],
                tool_name=tc["tool_name"],
                arguments=tc["arguments"],
            )
            for tc in d["tool_calls"]
        ]
    return LLMMessage(
        role=d["role"],
        content=d.get("content"),
        tool_calls=tool_calls,
        tool_call_id=d.get("tool_call_id"),
    )


class ConversationStore:
    """
    Loads and saves the full conversation history to disk.
    Each session is stored as a list of message dicts under a date-keyed entry.
    """

    def __init__(self, path: Path = HISTORY_FILE) -> None:
        self._path = path
        _ensure_dir()

    def load(self) -> list[LLMMessage]:
        """Load all past messages from disk (flattened across all sessions)."""
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            messages: list[LLMMessage] = []
            for session in raw.get("sessions", []):
                for msg_dict in session.get("messages", []):
                    # Skip system messages — we inject those fresh each time
                    if msg_dict.get("role") == "system":
                        continue
                    messages.append(_dict_to_msg(msg_dict))
            logger.info(f"Loaded {len(messages)} messages from history")
            return messages
        except Exception:
            logger.exception("Failed to load conversation history")
            return []

    def append_session(self, messages: list[LLMMessage]) -> None:
        """Append the current session's messages to the history file."""
        if not messages:
            return
        try:
            if self._path.exists():
                raw = json.loads(self._path.read_text(encoding="utf-8"))
            else:
                raw = {"sessions": []}

            session = {
                "started_at": datetime.now(UTC).isoformat(),
                "messages": [_msg_to_dict(m) for m in messages if m.role != "system"],
            }
            raw["sessions"].append(session)

            self._path.write_text(
                json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info(f"Saved session with {len(messages)} messages")
        except Exception:
            logger.exception("Failed to save conversation history")
