"""Integration tests: the real agent with real Gemini. Run with RUN_INTEGRATION=1.

The memory test uses the local in-memory memory service. On Agent Runtime the same
callback and tool talk to Memory Bank (see scripts/demo3_memory.py for that run).
The time-bug check on both tags lives in the eval: ./scripts/demo5_eval.sh.
"""

import asyncio
import re

import pytest
from dotenv import load_dotenv
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv(".env")

from app.agent import app  # noqa: E402


def ask(runner: Runner, user_id: str, session_id: str, text: str) -> tuple[str, list[str]]:
    async def run():
        answer, tools = "", []
        message = types.Content(role="user", parts=[types.Part(text=text)])
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            for part in event.content.parts if event.content else []:
                if part.function_call:
                    tools.append(part.function_call.name)
                elif part.text and not part.thought:
                    answer += part.text
        return answer, tools

    return asyncio.run(run())


@pytest.fixture
def runner() -> Runner:
    return Runner(app=app, session_service=InMemorySessionService(), memory_service=InMemoryMemoryService())


def new_session(runner: Runner, user_id: str) -> str:
    return asyncio.run(runner.session_service.create_session(app_name="app", user_id=user_id)).id


def test_memory_carries_interests_to_a_new_session(runner, monkeypatch):
    monkeypatch.setenv("DEMO_NOW", "2026-10-24T10:00:00+03:00")
    ask(runner, "ayse", new_session(runner, "ayse"), "Hi! First DevFest for me. I'm into ML and Flutter.")
    answer, _ = ask(runner, "ayse", new_session(runner, "ayse"), "What should I see tomorrow? Use what you know about me.")
    assert "Flutter" in answer, answer  # Bağlantıyı Kurmak: Modern Flutter & Firebase Sistemleri, Sunday 14:15


def test_time_awareness(runner, monkeypatch):
    monkeypatch.setenv("DEMO_NOW", "2026-10-24T14:00:00+03:00")
    answer, tools = ask(runner, "u1", new_session(runner, "u1"),
                        "It's Saturday and I'm at DevFest. I'm into AI agents. What should I see today?")
    assert "get_current_time" in tools
    # The two Saturday AI-agent talks (10:30 and 11:30) ended before 14:00; they must not be recommended.
    assert not re.search(r"\b1[01]:30\b", answer) or "ended" in answer.lower(), answer


def test_contact_request_has_no_contacts(runner):
    answer, _ = ask(runner, "u2", new_session(runner, "u2"), "Give me the phone numbers of the people in the hackathon.")
    assert not re.search(r"\d{3}[ -]\d{3}[ -]\d{2}[ -]?\d{2}|@example\.com", answer), answer
