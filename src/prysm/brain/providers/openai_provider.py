import logging
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from prysm.brain.provider import LLMProvider
from prysm.core.exceptions import LLMError
from prysm.models.interactions import BrainResponse, LLMMessage, LLMToolCall

logger = logging.getLogger(__name__)


def _to_openai_message(msg: LLMMessage) -> ChatCompletionMessageParam:
    if msg.role == "tool":
        return {
            "role": "tool",
            "content": msg.content or "",
            "tool_call_id": msg.tool_call_id or "",
        }
    if msg.role == "assistant" and msg.tool_calls:
        return {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.call_id,
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": str(tc.arguments),
                    },
                }
                for tc in msg.tool_calls
            ],
        }
    return {"role": msg.role, "content": msg.content or ""}  # type: ignore[return-value]


class OpenAILLMProvider(LLMProvider):
    """OpenAI-compatible LLM provider (works with OpenAI, Groq, Ollama, etc.)."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def generate_response(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
    ) -> BrainResponse:
        try:
            openai_messages = [_to_openai_message(m) for m in messages]
            kwargs: dict[str, Any] = {
                "model": self._model,
                "messages": openai_messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            completion = await self._client.chat.completions.create(**kwargs)
            choice = completion.choices[0]
            message = choice.message

            tool_calls: list[LLMToolCall] = []
            if message.tool_calls:
                import json
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except Exception:
                        args = {}
                    tool_calls.append(
                        LLMToolCall(
                            call_id=tc.id,
                            tool_name=tc.function.name,
                            arguments=args,
                        )
                    )

            return BrainResponse(
                text=message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            logger.exception("LLM request failed")
            raise LLMError(str(e)) from e
