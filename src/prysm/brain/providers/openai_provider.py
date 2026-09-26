import json
import logging
import re
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from prysm.brain.provider import LLMProvider
from prysm.core.exceptions import LLMError
from prysm.models.interactions import BrainResponse, LLMMessage, LLMToolCall

logger = logging.getLogger(__name__)

# Matches XML-style tool call blocks some models emit instead of proper JSON tool calls
_TOOL_CALL_XML_RE = re.compile(r"<tool_call>.*?</tool_call>", re.DOTALL)
# Also catch unclosed/partial tool call tags
_TOOL_CALL_TAG_RE = re.compile(r"</?tool_call>|</?function[^>]*>|</?parameter[^>]*>", re.DOTALL)


def _clean_response_text(text: str | None) -> str | None:
    """Strip any leaked XML tool call markup from the response text."""
    if not text:
        return text
    cleaned = _TOOL_CALL_XML_RE.sub("", text)
    cleaned = _TOOL_CALL_TAG_RE.sub("", cleaned)
    cleaned = cleaned.strip()
    return cleaned or None


def _to_openai_message(msg: LLMMessage) -> ChatCompletionMessageParam:
    if msg.role == "tool":
        return {
            "role": "tool",
            "content": msg.content or "",
            "tool_call_id": msg.tool_call_id or "",
            "name": getattr(msg, "name", None) or "unknown_tool",
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
                        # Must be valid JSON string — never use str() on a dict
                        "arguments": json.dumps(tc.arguments),
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
            result = await self._call(messages, tools)
            # If the model leaked XML tool calls into the text instead of using
            # the proper tool_calls field, retry without tools to get clean text.
            if result.text and _TOOL_CALL_XML_RE.search(result.text) and not result.tool_calls:
                logger.warning("Model leaked XML tool calls into text — retrying without tools")
                try:
                    return await self._call(messages, tools=None)
                except LLMError:
                    pass
            return result
        except LLMError as e:
            # Hard 400 from malformed tool generation — retry without tools.
            if tools and ("tool_use_failed" in str(e) or "400" in str(e)):
                logger.warning("Tool call failed — retrying without tools")
                try:
                    return await self._call(messages, tools=None)
                except LLMError:
                    pass
            raise

    async def _call(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None,
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
                text=_clean_response_text(message.content),
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
            )

        except Exception as e:
            logger.exception("LLM request failed")
            raise LLMError(str(e)) from e
