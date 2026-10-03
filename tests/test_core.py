"""Basic smoke tests for core components."""

import asyncio
import pytest

from prysm.core.events import EventBus, ResponseGenerated, StateChanged
from prysm.core.state import AssistantState
from prysm.models.interactions import BrainResponse, LLMMessage, UserInput
from prysm.brain.context import ContextManager
from prysm.tools.registry import ToolRegistry
from prysm.tools.executor import ToolExecutor


# ── EventBus ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe(ResponseGenerated, handler)
    await bus.publish(ResponseGenerated(response_text="hello"))
    assert len(received) == 1
    assert received[0].response_text == "hello"


@pytest.mark.asyncio
async def test_event_bus_no_handler():
    bus = EventBus()
    # Should not raise even with no subscribers
    await bus.publish(ResponseGenerated(response_text="test"))


# ── ContextManager ────────────────────────────────────────────────────────────

def test_context_manager_messages():
    ctx = ContextManager()
    ctx.add_user_message("Hello")
    ctx.add_assistant_message("Hi there!")
    messages = ctx.get_messages()
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[2].role == "assistant"


def test_context_manager_clear():
    ctx = ContextManager()
    ctx.add_user_message("test")
    ctx.clear()
    messages = ctx.get_messages()
    assert len(messages) == 1  # only system prompt


# ── Models ────────────────────────────────────────────────────────────────────

def test_user_input_defaults():
    inp = UserInput(text="hello")
    assert inp.source == "text"
    assert inp.text == "hello"


def test_brain_response_defaults():
    r = BrainResponse(text="hi")
    assert r.finish_reason == "stop"
    assert r.tool_calls == []


# ── ToolRegistry ──────────────────────────────────────────────────────────────

def test_tool_registry_register_and_list():
    from prysm.tools.interfaces import BaseTool
    from typing import Any

    class DummyTool(BaseTool):
        def get_schemas(self):
            return [{"name": "dummy", "description": "test", "parameters": {"type": "object", "properties": {}, "required": []}}]
        async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
            return "ok"

    registry = ToolRegistry()
    DummyTool().register(registry)
    assert "dummy" in registry.list_tools()


# ── Voice Pipeline & Stop Detection ──────────────────────────────────────────

def test_is_stop_command():
    from prysm.audio.pipeline import is_stop_command

    # Positive matches (with varied case, whitespace, and punctuation)
    assert is_stop_command("stop")
    assert is_stop_command("STOP!")
    assert is_stop_command("  stop.  ")
    assert is_stop_command("stop talking")
    assert is_stop_command("shut up")
    assert is_stop_command("be quiet!")
    assert is_stop_command("that's enough")
    assert is_stop_command("thats enough")
    assert is_stop_command("never mind")

    # Negative matches (longer sentences, full queries, general speech)
    assert not is_stop_command("can you stop the music")
    assert not is_stop_command("please stop doing that and tell me the weather")
    assert not is_stop_command("what is the stop sign")
    assert not is_stop_command("hello PRYSM")

