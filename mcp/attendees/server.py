"""A tiny MCP server with fictional attendee contacts. It exists only to be blocked.

Deployed to Cloud Run with IAM-only access: callers need roles/run.invoker.
"""

import json
import os
from pathlib import Path

from fastmcp import FastMCP

ATTENDEES = json.loads((Path(__file__).parent / "attendees.json").read_text())["attendees"]

mcp = FastMCP("devfest-attendees")


@mcp.tool
def get_attendee_contacts(name: str = "") -> list[dict]:
    """Returns email and phone of DevFest attendees whose name or hackathon team matches."""
    name = name.lower()
    return [a for a in ATTENDEES if name in a["name"].lower() or name in a["hackathon_team"].lower()]


if __name__ == "__main__":
    # Cloud Run already checks who may call us, so skip DNS-rebinding host checks.
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")),
            stateless_http=True, host_origin_protection=False)
