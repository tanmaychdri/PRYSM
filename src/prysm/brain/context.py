import logging

from prysm.models.interactions import LLMMessage, LLMToolCall, ToolExecutionResult

logger = logging.getLogger(__name__)

_BASE_SYSTEM_PROMPT = """You are PRYSM, a fast, capable, and friendly personal AI assistant running locally on the user's Windows PC.
You can control the operating system, answer questions, and have natural conversations.
Be concise and direct. When you use tools, don't narrate what you're doing — just do it and report the result briefly.
Today's date and time are available via the get_system_info tool if needed.

You have a persistent memory of the user across all sessions. Use it naturally — reference past projects, \
preferences, and context without being asked. If the user mentions something that updates your memory, \
acknowledge it and remember it.

## What you remember about the user:
{memory}"""


class ContextManager:
    """
    Manages the conversation message history sent to the LLM.
    Integrates with ConversationStore (persistent history) and LongTermMemory (facts).
    """

    def __init__(
        self,
        long_term_memory=None,   # LongTermMemory | None
        conversation_store=None, # ConversationStore | None
        max_recent_messages: int = 40,
        max_history_messages: int = 20,
    ) -> None:
        self._memory = long_term_memory
        self._store = conversation_store
        self._max_recent = max_recent_messages
        self._max_history = max_history_messages

        # Current session messages
        self._messages: list[LLMMessage] = []

        # Load recent history from previous sessions
        if self._store:
            past = self._store.load()
            # Only keep the tail of history to avoid huge contexts
            self._history: list[LLMMessage] = past[-self._max_history:]
            logger.info(f"Loaded {len(self._history)} messages from past sessions")
        else:
            self._history = []

    # ------------------------------------------------------------------
    # Message management
    # ------------------------------------------------------------------

    def add_user_message(self, text: str) -> None:
        self._messages.append(LLMMessage(role="user", content=text))
        self._trim()

    def add_assistant_message(
        self,
        text: str | None = None,
        tool_calls: list[LLMToolCall] | None = None,
    ) -> None:
        self._messages.append(
            LLMMessage(role="assistant", content=text, tool_calls=tool_calls or None)
        )

    def add_tool_result(self, result: ToolExecutionResult) -> None:
        content = str(result.result) if result.success else f"Error: {result.error_message}"
        self._messages.append(
            LLMMessage(role="tool", content=content, tool_call_id=result.call_id)
        )

    def get_messages(self) -> list[LLMMessage]:
        """Return system prompt + history + current session messages."""
        memory_text = self._memory.format_for_prompt() if self._memory else "(none)"
        system = LLMMessage(
            role="system",
            content=_BASE_SYSTEM_PROMPT.format(memory=memory_text),
        )
        return [system] + self._history + self._messages

    def get_session_messages(self) -> list[LLMMessage]:
        """Return only the current session's messages (for memory extraction)."""
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        if len(self._messages) > self._max_recent:
            self._messages = self._messages[-self._max_recent:]

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    def save_session(self) -> None:
        """Persist the current session to disk."""
        if self._store and self._messages:
            self._store.append_session(self._messages)

    def format_session_as_text(self) -> str:
        """Format current session as plain text for memory extraction."""
        lines = []
        for msg in self._messages:
            if msg.role == "user":
                lines.append(f"User: {msg.content}")
            elif msg.role == "assistant" and msg.content:
                lines.append(f"PRYSM: {msg.content}")
        return "\n".join(lines)
