"""Finds the Cloud Trace trace of one agent session and prints its waterfall and console link.

Usage: uv run python scripts/trace_link.py [SESSION_ID]   (default: artifacts/last_session.txt)
"""

import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import google.auth
import google.auth.transport.requests
import requests
from agent_client import project

SHOW = ("invoke_agent", "retrieve_memories", "save_memories", "generate_content", "execute_tool")


def find_trace(session_id: str, headers: dict) -> dict | None:
    start = (datetime.now(UTC) - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"https://cloudtrace.googleapis.com/v1/projects/{project()}/traces"
    for _ in range(12):  # traces arrive a few seconds after the request
        params = {"filter": f"+gen_ai.conversation.id:{session_id}", "startTime": start, "pageSize": 100}
        for _ in range(20):  # the API can return empty pages before the match
            page = requests.get(url, headers=headers, params=params, timeout=30).json()
            if page.get("traces"):
                trace_id = page["traces"][0]["traceId"]
                return requests.get(f"{url}/{trace_id}", headers=headers, timeout=30).json()
            if not page.get("nextPageToken"):
                break
            params["pageToken"] = page["nextPageToken"]
        time.sleep(5)
    return None


def main() -> None:
    session_id = sys.argv[1] if len(sys.argv) > 1 else Path("artifacts/last_session.txt").read_text().strip()
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {"Authorization": f"Bearer {credentials.token}", "x-goog-user-project": project()}

    trace = find_trace(session_id, headers)
    if not trace:
        sys.exit(f"❌ No trace yet for session {session_id}. Try again in a few seconds.")
    spans = sorted(trace["spans"], key=lambda s: s["startTime"])
    t0 = datetime.fromisoformat(spans[0]["startTime"])
    print(f"\n\033[1m🔎 Trace of session {session_id}\033[0m\n")
    for span in spans:
        if not span["name"].startswith(SHOW) or span["name"] == "execute_tool (merged)":
            continue
        start = (datetime.fromisoformat(span["startTime"]) - t0).total_seconds()
        length = (datetime.fromisoformat(span["endTime"]) - datetime.fromisoformat(span["startTime"])).total_seconds()
        bar = " " * int(start * 2) + "█" * max(1, int(length * 2))
        print(f"  {span['name'][:34]:34} {length:5.1f}s  \033[36m{bar[:60]}\033[0m")
    link = f"https://console.cloud.google.com/traces/explorer;traceId={trace['traceId']}?project={project()}"
    print(f"\n\033[1m👉 {link}\033[0m\n")


if __name__ == "__main__":
    main()
