import json
import logging
from typing import Any

from openai import AsyncOpenAI

from prysm.brain.provider import LLMProvider
from prysm.models.interactions import BrainResponse, LLMToolCall

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """LLM Provider implementation using the official OpenAI client.
    Can be configured to point to local OpenAI-compatible APIs like Ollama/vLLM.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None,
        )
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate_response(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
    ) -> BrainResponse:
        """Generate a response using the OpenAI Chat Completions API."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }

            if tools:
                kwargs["tools"] = tools

            logger.info(
                f"Calling LLM provider '{self.model}' with {len(messages)} messages."
            )
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]

            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    # Parse arguments robustly
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Failed to parse arguments for tool {tc.function.name}. Passing raw string."
                        )
                        args = {"raw_arguments": tc.function.arguments}

                    tool_calls.append(
                        LLMToolCall(
                            call_id=tc.id,
                            tool_name=tc.function.name,
                            arguments=args,
                        )
                    )

            return BrainResponse(
                text=choice.message.content,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason or "stop",
                metadata={
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens
                        if response.usage
                        else 0,
                        "completion_tokens": response.usage.completion_tokens
                        if response.usage
                        else 0,
                        "total_tokens": response.usage.total_tokens
                        if response.usage
                        else 0,
                    },
                },
            )

        except Exception:
            logger.exception("Error calling OpenAI provider.")
            raise
