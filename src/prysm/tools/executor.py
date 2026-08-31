import asyncio
import logging
import time

from prysm.models.interactions import LLMToolCall, ToolExecutionResult
from prysm.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tools safely with validation, timeout, and result normalization."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute(
        self, tool_call: LLMToolCall, timeout_s: float = 30.0
    ) -> ToolExecutionResult:
        """Execute a tool call safely."""
        start_time = time.time()
        tool = self.registry.get_tool(tool_call.tool_name)

        if not tool:
            logger.warning(f"Unknown tool requested: {tool_call.tool_name}")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error_message=f"UnknownTool: Tool '{tool_call.tool_name}' is not registered.",
                duration_s=time.time() - start_time,
            )

        # TODO: Real confirmation mechanism via UI/Voice
        if tool.requires_confirmation:
            logger.info(
                f"Tool {tool_call.tool_name} requires confirmation. Auto-confirming for now."
            )

        try:
            logger.info(
                f"Executing tool {tool_call.tool_name} with args: {tool_call.arguments}"
            )

            # Execute with timeout
            async with asyncio.timeout(timeout_s):
                result = await tool.execute(**tool_call.arguments)

            logger.info(f"Tool {tool_call.tool_name} completed successfully.")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=result,
                success=True,
                duration_s=time.time() - start_time,
                metadata={"risk": tool.risk_level.value},
            )

        except TimeoutError:
            logger.error(f"Tool {tool_call.tool_name} timed out after {timeout_s}s.")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error_message=f"ToolTimeout: Tool '{tool_call.tool_name}' timed out after {timeout_s} seconds.",
                duration_s=time.time() - start_time,
            )
        except asyncio.CancelledError:
            logger.warning(f"Tool {tool_call.tool_name} execution was cancelled.")
            raise
        except Exception as e:
            logger.exception(f"Tool {tool_call.tool_name} failed with error: {e}")
            return ToolExecutionResult(
                call_id=tool_call.call_id,
                tool_name=tool_call.tool_name,
                result=None,
                success=False,
                error_message=f"ToolError: {str(e)}",
                duration_s=time.time() - start_time,
            )
