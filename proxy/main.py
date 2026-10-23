"""samsun-chat-proxy: lets phones chat with the deployed agent without any Google credentials.

Browser (omarcevi.dev) -> this proxy on Cloud Run -> Agent Runtime (one agent, AGENT_ID).
The proxy calls Agent Runtime as its own service account and adds the limits a public demo needs.
"""

import asyncio
import json
import os
import re
import time
import uuid
from collections import defaultdict, deque

import google.auth
import google.auth.transport.requests
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("AGENT_LOCATION", "us-central1")
AGENT_ID = os.environ["AGENT_ID"]  # numeric id or full resource name
ENGINE = AGENT_ID if "/" in AGENT_ID else f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ID}"
API = f"https://{LOCATION}-aiplatform.googleapis.com"
REPO_URL = "https://github.com/omarcevi/devfest-samsun-assistant"

CHAT_ENABLED = os.environ.get("CHAT_ENABLED", "true").lower() == "true"
MAX_CHARS = int(os.environ.get("MAX_CHARS", "500"))
MAX_TURNS = int(os.environ.get("MAX_TURNS", "20"))
PER_MINUTE = int(os.environ.get("PER_MINUTE", "6"))  # per user
PER_DAY = int(os.environ.get("PER_DAY", "60"))  # per user
# Venue Wi-Fi puts the whole room behind one IP, so the per-IP limit is much looser.
IP_PER_MINUTE = int(os.environ.get("IP_PER_MINUTE", "40"))
IP_PER_DAY = int(os.environ.get("IP_PER_DAY", "1500"))
GLOBAL_PER_MINUTE = int(os.environ.get("GLOBAL_PER_MINUTE", "80"))  # Agent Runtime allows 90 queries/min
GLOBAL_PER_DAY = int(os.environ.get("GLOBAL_PER_DAY", "4000"))
ENDED_MESSAGE = "The DevFest Samsun demo has ended. The code is on GitHub."

app = FastAPI(title="samsun-chat-proxy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://omarcevi.dev", "https://www.omarcevi.dev"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
client = httpx.AsyncClient(timeout=httpx.Timeout(120, connect=10))
hits: dict[str, deque] = defaultdict(deque)  # key -> timestamps of recent messages
sessions: dict[str, dict] = {}  # session_id -> {"user_id", "turns"}

# Everything below runs on one instance (max-instances=1), so in-memory limits are exact.


class SessionIn(BaseModel):
    user_id: str


class ChatIn(BaseModel):
    user_id: str
    session_id: str
    message: str


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)


def valid_user(user_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9-]{8,64}", user_id))


def agent_user(user_id: str) -> str:
    """Public users get a prefix so their memories are easy to find and delete."""
    return f"web-{user_id}"


def over_limit(key: str, per_minute: int, per_day: int) -> bool:
    now = time.time()
    stamps = hits[key]
    while stamps and stamps[0] < now - 86400:
        stamps.popleft()
    last_minute = sum(1 for t in stamps if t > now - 60)
    return last_minute >= per_minute or len(stamps) >= per_day


def client_ip(request: Request) -> str:
    """Cloud Run appends the real client IP last; earlier entries can be spoofed."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[-1].strip() or (request.client.host if request.client else "?")


def record(keys: list[tuple[str, int, int]]) -> bool:
    """Counts one request against each key. Returns False if any key is over its limit."""
    if any(over_limit(key, per_minute, per_day) for key, per_minute, per_day in keys):
        return False
    for key, _, _ in keys:
        hits[key].append(time.time())
    if len(hits) > 50_000:  # keep memory bounded: drop keys idle for a day
        for key in [k for k, v in hits.items() if not v or v[-1] < time.time() - 86400]:
            del hits[key]
    return True


async def auth_headers() -> dict:
    if not credentials.valid:
        await asyncio.to_thread(credentials.refresh, google.auth.transport.requests.Request())
    return {"Authorization": f"Bearer {credentials.token}", "Content-Type": "application/json"}


@app.get("/api/status")
async def status() -> dict:
    return {"enabled": CHAT_ENABLED, "message": "" if CHAT_ENABLED else ENDED_MESSAGE, "repo": REPO_URL}


@app.post("/api/session")
async def create_session(body: SessionIn, request: Request):
    if not CHAT_ENABLED:
        return error(403, "ended", ENDED_MESSAGE)
    if not valid_user(body.user_id):
        return error(400, "bad_user", "Invalid user id.")
    # Creating a session is also an Agent Runtime query, so it counts toward the global budget.
    if not record([("session-ip:" + client_ip(request), IP_PER_MINUTE, IP_PER_DAY),
                   ("global", GLOBAL_PER_MINUTE, GLOBAL_PER_DAY)]):
        return error(429, "rate_limited", "Too many new chats. Wait a minute and try again.")
    payload = {"class_method": "async_create_session", "input": {"user_id": agent_user(body.user_id)}}
    response = await client.post(f"{API}/v1/{ENGINE}:query", headers=await auth_headers(), json=payload)
    if response.status_code != 200:
        return error(502, "upstream", "The assistant is not reachable right now. Try again in a minute.")
    session_id = response.json()["output"]["id"]
    if len(sessions) > 50_000:
        sessions.pop(next(iter(sessions)))  # forget the oldest chat
    sessions[session_id] = {"user_id": body.user_id, "turns": 0}
    return {"session_id": session_id}


@app.post("/api/chat")
async def chat(body: ChatIn, request: Request):
    if not CHAT_ENABLED:
        return error(403, "ended", ENDED_MESSAGE)
    message = body.message.strip()
    if not message:
        return error(400, "empty", "Type a question first.")
    if len(message) > MAX_CHARS:
        return error(400, "too_long", f"Please keep it under {MAX_CHARS} characters.")
    session = sessions.get(body.session_id)
    if not session or session["user_id"] != body.user_id:
        return error(409, "session_expired", "This chat expired. Starting a new one.")
    if session["turns"] >= MAX_TURNS:
        return error(409, "session_full", f"This chat reached {MAX_TURNS} messages. Tap New chat to continue.")
    keys = [("ip:" + client_ip(request), IP_PER_MINUTE, IP_PER_DAY), ("user:" + body.user_id, PER_MINUTE, PER_DAY),
            ("global", GLOBAL_PER_MINUTE, GLOBAL_PER_DAY)]
    if not record(keys):
        return error(429, "rate_limited", "Lots of questions right now! Wait a minute and try again.")
    session["turns"] += 1
    return StreamingResponse(relay(body, message), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def relay(body: ChatIn, message: str):
    """Streams the agent's events to the browser as small SSE messages: text, tool, done, error."""
    payload = {
        "class_method": "async_stream_query",
        "input": {"user_id": agent_user(body.user_id), "session_id": body.session_id,
                  "message": message, "run_config": {"streaming_mode": "sse"}},
    }
    streamed_text = False
    try:
        url = f"{API}/v1/{ENGINE}:streamQuery?alt=sse"
        async with client.stream("POST", url, headers=await auth_headers(), json=payload) as response:
            if response.status_code != 200:
                code = "busy" if response.status_code == 429 else "upstream"
                yield sse({"type": "error", "code": code})
                return
            async for line in response.aiter_lines():
                event = parse_event(line)
                for part in (event.get("content") or {}).get("parts") or []:
                    if (call := part.get("function_call")) and not event.get("partial"):
                        streamed_text = False
                        yield sse({"type": "tool", "name": call.get("name")})
                    elif (text := part.get("text")) and not part.get("thought"):
                        if event.get("partial"):
                            streamed_text = True
                            yield sse({"type": "text", "text": text})
                        elif not streamed_text:  # the final event repeats streamed text
                            yield sse({"type": "text", "text": text})
    except httpx.HTTPError:
        yield sse({"type": "error", "code": "upstream"})
        return
    yield sse({"type": "done"})


def parse_event(line: str) -> dict:
    line = line.strip()
    if line.startswith("data:"):
        line = line[5:].strip()
    if not line.startswith("{"):
        return {}
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {}


def sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/forget")
async def forget(body: SessionIn, request: Request):
    """Deletes this user's Memory Bank memories."""
    if not valid_user(body.user_id):
        return error(400, "bad_user", "Invalid user id.")
    if not record([("forget-ip:" + client_ip(request), 20, 200)]):
        return error(429, "rate_limited", "Wait a minute and try again.")
    payload = {"filter": f'scope.user_id="{agent_user(body.user_id)}"', "force": True}
    response = await client.post(f"{API}/v1beta1/{ENGINE}/memories:purge", headers=await auth_headers(), json=payload)
    if response.status_code != 200:
        return error(502, "upstream", "Could not delete memories right now. Try again in a minute.")
    for session_id in [s for s, v in sessions.items() if v["user_id"] == body.user_id]:
        sessions.pop(session_id)
    return {"forgotten": True, "new_user_id": str(uuid.uuid4())}


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
