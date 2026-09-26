import logging
import time

from prysm.core.exceptions import ToolNotFoundError
from prysm.models.interactions import LLMToolCall, ToolExecutionResult
from prysm.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls by dispatching to the registered handler."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_call: LLMToolCall) -> ToolExecutionResult:
        start = time.perf_counter()
        try:
            handler = self._registry.get_handler(tool_call.tool_name)
            result = await handler.execute(tool_call.tool_name, tool_call.arguments)
            duration = time.perf_counter() - start
            logger.debug(f"Tool '{tool_call.tool_name}' completed in {duration:.3f}s")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=result,
                success=True,
                duration_s=duration,
            )
        except ToolNotFoundError as e:
            logger.error(f"Tool not found: {tool_call.tool_name}")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.exception(f"Tool '{tool_call.tool_name}' raised an error")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error_message=str(e),
            )
