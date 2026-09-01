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

        args = dict(tool_call.arguments)
        
        # Intercept for confirmation
        if tool.requires_confirmation:
            if not args.pop("_confirmed", False):
                logger.info(f"Tool {tool_call.tool_name} requires confirmation. Returning prompt to LLM.")
                return ToolExecutionResult(
                    call_id=tool_call.call_id,
                    tool_name=tool_call.tool_name,
                    result=None,
                    success=False,
                    error_message=(
                        "ConfirmationRequired: This tool modifies system state and requires explicit user confirmation. "
                        "Please tell the user exactly what you are about to do, including the arguments, and ask them if it is OK. "
                        "Once they confirm, call this tool again and add '_confirmed': true to the arguments."
                    ),
                    duration_s=time.time() - start_time,
                    metadata={"risk": tool.risk_level.value},
                )
            else:
                logger.info(f"Tool {tool_call.tool_name} executing with explicit confirmation.")

        try:
            logger.info(f"Executing tool {tool_call.tool_name} with args: {args}")

            # Execute with timeout
            async with asyncio.timeout(timeout_s):
                result = await tool.execute(**args)

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
