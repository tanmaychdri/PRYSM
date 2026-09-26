import logging
from typing import Any

from prysm.models.interactions import LLMMessage, LLMToolCall, ToolExecutionResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are PRYSM, a fast, capable, and friendly personal AI assistant running locally on the user's Windows PC.
You can control the operating system, answer questions, and have natural conversations.
Be concise and direct. When you use tools, don't narrate what you're doing — just do it and report the result briefly.
Today's date and time are available via the get_system_info tool if needed."""


class ContextManager:
    """Manages the conversation message history sent to the LLM."""

    def __init__(self, system_prompt: str = SYSTEM_PROMPT, max_messages: int = 40) -> None:
        self._system_prompt = system_prompt
        self._max_messages = max_messages
        self._messages: list[LLMMessage] = []

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
        system = LLMMessage(role="system", content=self._system_prompt)
        return [system] + self._messages

    def clear(self) -> None:
        self._messages.clear()

    def _trim(self) -> None:
        if len(self._messages) > self._max_messages:
            # Keep the most recent messages, always preserve tool result pairs
            self._messages = self._messages[-self._max_messages :]
