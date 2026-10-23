"""Optional remote tool: attendee contacts from a separate MCP server on Cloud Run.

It is only added when ATTENDEES_MCP_URL is set (the speaker's demo instance).
Lab participants never set it. The code is wired to the server on purpose:
the platform's policy, not the prompt, decides whether the call goes through.
"""

import logging
import os

import google.auth.transport.requests
from google.oauth2 import id_token
from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

ATTENDEES_MCP_URL = os.environ.get("ATTENDEES_MCP_URL", "").rstrip("/")


async def get_attendee_contacts(name: str) -> dict:
    """Looks up the email and phone number of DevFest attendees.

    Args:
        name: Part of a name, or a hackathon team such as "Team Martı". Use "" for everyone.
    """
    try:
        client = create_mcp_http_client(headers=_auth_headers())
        async with streamable_http_client(f"{ATTENDEES_MCP_URL}/mcp", http_client=client) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                result = await session.call_tool("get_attendee_contacts", {"name": name})
        return {"contacts": result.content[0].text}
    except Exception as error:  # a 403 here means policy blocked the call
        reason = _root_cause(error)
        logging.warning("get_attendee_contacts denied: %s", reason)
        return {"error": f"The attendee directory refused the request: {reason}"}


def _auth_headers() -> dict:
    """An ID token for the Cloud Run service, if this identity can mint one."""
    try:
        # Agent Identity tokens are certificate-bound by default; a plain *.run.app URL needs an unbound one.
        token = id_token.fetch_id_token(
            google.auth.transport.requests.Request(), ATTENDEES_MCP_URL, bind_id_token=False
        )
        return {"Authorization": f"Bearer {token}"}
    except Exception as error:
        logging.warning("Could not mint an ID token: %s", error)
        return {}


def _root_cause(error: BaseException) -> str:
    """MCP errors arrive wrapped in exception groups; return the innermost message."""
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    return f"{type(error).__name__}: {error}"


attendee_tools = [get_attendee_contacts] if ATTENDEES_MCP_URL else []
