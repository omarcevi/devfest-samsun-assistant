"""Tiny client for a deployed Agent Runtime agent, shared by the demo scripts.

Which agent: AGENT_ID (numeric id or full resource name) or, if unset, the one in
deployment_metadata.json written by `agents-cli deploy`.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import google.auth
import google.auth.transport.requests
import requests

ROOT = Path(__file__).resolve().parent.parent
LOCATION = os.environ.get("AGENT_LOCATION", "us-central1")
API = f"https://{LOCATION}-aiplatform.googleapis.com"


def project() -> str:
    return os.environ.get("GOOGLE_CLOUD_PROJECT") or subprocess.run(
        ["gcloud", "config", "get-value", "project"], capture_output=True, text=True
    ).stdout.strip()


def engine() -> str:
    agent_id = os.environ.get("AGENT_ID", "")
    if not agent_id:
        metadata = ROOT / "deployment_metadata.json"
        agent_id = json.loads(metadata.read_text()).get("remote_agent_runtime_id", "") if metadata.exists() else ""
    if not agent_id:
        sys.exit("❌ No agent. Set AGENT_ID or run `agents-cli deploy` first.")
    if "/" in agent_id:
        return agent_id
    return f"projects/{project()}/locations/{LOCATION}/reasoningEngines/{agent_id}"


def _headers() -> dict:
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(google.auth.transport.requests.Request())
    return {"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json",
            "x-goog-user-project": project()}


def create_session(user_id: str) -> str:
    body = {"class_method": "async_create_session", "input": {"user_id": user_id}}
    response = requests.post(f"{API}/v1/{engine()}:query", headers=_headers(), json=body, timeout=60)
    response.raise_for_status()
    return response.json()["output"]["id"]


def ask(user_id: str, session_id: str, message: str):
    """Yields ("tool", name) and ("text", text) as the agent works."""
    body = {"class_method": "async_stream_query",
            "input": {"user_id": user_id, "session_id": session_id, "message": message}}
    url = f"{API}/v1/{engine()}:streamQuery?alt=sse"
    with requests.post(url, headers=_headers(), json=body, stream=True, timeout=180) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            line = (line or "").removeprefix("data:").strip()
            if not line.startswith("{"):
                continue
            for part in (json.loads(line).get("content") or {}).get("parts") or []:
                if part.get("function_call"):
                    yield "tool", part["function_call"]["name"]
                elif part.get("text") and not part.get("thought"):
                    yield "text", part["text"]


def memories(user_id: str) -> list[str]:
    """The facts Memory Bank stored for this user."""
    body = {"scope": {"app_name": "app", "user_id": user_id}}
    response = requests.post(f"{API}/v1beta1/{engine()}/memories:retrieve", headers=_headers(), json=body, timeout=60)
    response.raise_for_status()
    return [m["memory"]["fact"] for m in response.json().get("retrievedMemories", [])]


def purge_memories(user_id: str) -> None:
    body = {"filter": f'scope.user_id="{user_id}"', "force": True}
    response = requests.post(f"{API}/v1beta1/{engine()}/memories:purge", headers=_headers(), json=body, timeout=60)
    response.raise_for_status()


def console_url() -> str:
    location, agent_id = engine().split("/")[3], engine().split("/")[5]
    return (f"https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/{location}"
            f"/agent-engines/{agent_id}?project={project()}")
