import json
import logging
from typing import Any

from prysm.models.interactions import (
    Conversation,
    LLMMessage,
    LLMToolCall,
    ToolExecutionResult,
)

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages LLM conversation context, memory, and truncation."""

    def __init__(self, max_history: int = 20):
        self.conversation = Conversation()
        self.max_history = max_history
        self._system_prompt = "You are PRYSM, a helpful desktop AI assistant."

    def set_system_prompt(self, prompt: str) -> None:
        """Set the default system prompt."""
        self._system_prompt = prompt

    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation."""
        self.conversation.add_message(LLMMessage(role="user", content=text))
        self._truncate_history()

    def add_assistant_message(
        self, text: str | None = None, tool_calls: list[LLMToolCall] | None = None
    ) -> None:
        """Add an assistant message (text or tool calls)."""
        self.conversation.add_message(
            LLMMessage(role="assistant", content=text, tool_calls=tool_calls)
        )
        self._truncate_history()

    def add_tool_result(self, result: ToolExecutionResult) -> None:
        """Add a tool execution result to the conversation."""
        content = (
            str(result.result) if result.success else f"Error: {result.error_message}"
        )
        self.conversation.add_message(
            LLMMessage(
                role="tool",
                content=content,
                tool_call_id=result.call_id,
            )
        )
        self._truncate_history()

    def get_messages(self) -> list[dict[str, Any]]:
        """Get normalized messages ready for the LLM Provider."""
        # Always inject the system prompt at the very beginning
        messages = [{"role": "system", "content": self._system_prompt}]

        for msg in self.conversation.messages:
            msg_dict: dict[str, Any] = {"role": msg.role}
            if msg.content is not None:
                msg_dict["content"] = msg.content

            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.call_id,
                        "type": "function",
                        "function": {
                            "name": tc.tool_name,
                            "arguments": json.dumps(tc.arguments)
                            if isinstance(tc.arguments, dict)
                            else tc.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id

            messages.append(msg_dict)

        return messages

    def _truncate_history(self) -> None:
        """Keep the conversation history within bounds."""
        if len(self.conversation.messages) > self.max_history:
            # Drop the oldest messages, keeping the most recent max_history
            logger.debug(f"Truncating history to last {self.max_history} messages.")
            self.conversation.messages = self.conversation.messages[-self.max_history :]
