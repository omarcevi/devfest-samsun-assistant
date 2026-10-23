"""Long-term memory, with trace spans so each memory step shows up in Cloud Trace.

Locally the memory store is in-memory. On Agent Runtime it is Memory Bank, which
extracts facts ("likes ML and Flutter") and returns them in later sessions.
"""

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import preload_memory_tool
from opentelemetry import trace

tracer = trace.get_tracer("samsun_assistant")


class PreloadMemoryTool(preload_memory_tool.PreloadMemoryTool):
    """ADK's PreloadMemoryTool: before each model call, adds what we remember about the user."""

    async def process_llm_request(self, *, tool_context, llm_request) -> None:
        with tracer.start_as_current_span("retrieve_memories"):
            await super().process_llm_request(tool_context=tool_context, llm_request=llm_request)


async def save_to_memory(callback_context: CallbackContext) -> None:
    """Runs after the agent answers. Memory Bank generates memories in the background."""
    with tracer.start_as_current_span("save_memories"):
        await callback_context.add_session_to_memory()
