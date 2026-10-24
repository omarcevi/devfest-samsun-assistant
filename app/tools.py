"""Tools the agent can call. ADK builds each tool's schema from its type hints and docstring."""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

AGENDA = json.loads((Path(__file__).parent.parent / "data" / "agenda.json").read_text())
SESSIONS = AGENDA["sessions"]
FEEDBACK: dict[str, list[int]] = {}  # session_id -> ratings, kept in memory


def search_sessions(topic: str, day: str, after: str = "") -> list[dict]:
    """Finds DevFest Samsun 2026 sessions about a topic on one day.
    Args:
        topic: A topic such as "ai", "flutter" or "security". Use "" for every session.
        day: "2026-10-24" (Saturday) or "2026-10-25" (Sunday).
        after: Optional "HH:MM". Only returns sessions starting at or after this time.
    """
    words = topic.lower().split()
    return [
        {"id": s["id"], "title": s["title"], "speaker": s["speaker"],
         "start": s["start"], "floor": s["floor"]}
        for s in SESSIONS
        if s["day"] == day and s["start"] >= after
        and (not words or any(w in s["tags"] or w in s["title"].lower() for w in words))
    ]


def get_session(session_id: str) -> dict:
    """Gets the full details of one session: title, speaker, day, time and floor.

    Args:
        session_id: The session id returned by search_sessions, e.g. "sat-1030-kat2".
    """
    for session in SESSIONS:
        if session["id"] == session_id:
            return session
    return {"error": f"No session with id '{session_id}'. Use search_sessions first."}


def submit_feedback(session_id: str, rating: int) -> dict:
    """Records the user's 1-5 star rating for a session.

    Args:
        session_id: The session id, e.g. "sat-1030-kat2".
        rating: A whole number from 1 (poor) to 5 (excellent).
    """
    if not 1 <= rating <= 5:
        return {"error": "The rating must be between 1 and 5."}
    if not any(s["id"] == session_id for s in SESSIONS):
        return {"error": f"No session with id '{session_id}'."}
    FEEDBACK.setdefault(session_id, []).append(rating)
    return {"status": "saved", "session_id": session_id, "rating": rating}


def get_current_time() -> str:
    """Returns the current day, date and time at DevFest Samsun (Europe/Istanbul)."""
    # DEMO_NOW pins the clock for a reproducible demo, e.g. 2026-10-24T14:00:00+03:00
    demo_now = os.environ.get("DEMO_NOW")
    now = datetime.fromisoformat(demo_now) if demo_now else datetime.now(ZoneInfo("Europe/Istanbul"))
    return now.strftime("%A %Y-%m-%d %H:%M")
