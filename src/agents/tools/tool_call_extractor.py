"""Tool call extraction utilities.

This module provides a centralized tool call extraction utility
to eliminate code duplication across the codebase.
"""

from typing import Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


class ToolCallExtractor:
    """Extracts tool calls from Pydantic AI agent results.

    This class provides a centralized utility for extracting tool call
    information from agent results, eliminating code duplication between
    agents/service.py and chat/stream.py.
    """

    @staticmethod
    def extract(result) -> List[Dict[str, Any]]:
        """
        Extract tool calls from agent result.

        Args:
            result: Pydantic AI agent result object

        Returns:
            List of tool call dictionaries with keys:
            - tool_name: Name of the tool
            - args: Tool arguments as dict
            - tool_call_id: Optional tool call ID
        """
        tools_used = []
        try:
            messages = result.all_messages()
            for message in messages:
                if hasattr(message, "parts"):
                    for part in message.parts:
                        if part.__class__.__name__ == "ToolCallPart":
                            tool_name = str(getattr(part, "tool_name", "unknown"))
                            tool_args = ToolCallExtractor._extract_args(part)
                            tool_call_id = (
                                str(getattr(part, "tool_call_id", ""))
                                if hasattr(part, "tool_call_id") and part.tool_call_id
                                else None
                            )
                            tools_used.append({
                                "tool_name": tool_name,
                                "args": tool_args,
                                "tool_call_id": tool_call_id,
                            })
        except Exception as e:
            logger.warning(f"Failed to extract tool calls: {e}")

        return tools_used

    @staticmethod
    def _extract_args(part) -> Dict[str, Any]:
        """
        Extract tool arguments from a part object.

        Args:
            part: ToolCallPart object

        Returns:
            Dictionary of tool arguments
        """
        tool_args = {}
        if hasattr(part, "args") and part.args is not None:
            if isinstance(part.args, str):
                try:
                    tool_args = json.loads(part.args)
                except json.JSONDecodeError:
                    pass
            elif isinstance(part.args, dict):
                tool_args = part.args
        return tool_args
