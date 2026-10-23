"""Custom eval metric: runs the checks each eval case lists in its "metadata".

Supported keys in a case's metadata:
  tool, args   the agent must call this tool with these arguments
  mentions     strings the final answer must contain
  no_contacts  the answer must not contain an email address or phone number
  rubric       a rule an LLM judge (Gemini) checks the answer against

Every case is also checked for invented sessions against data/agenda.json.
agents-cli runs this file from the project root, as source (no __file__).
"""

import json
import re
import threading
from pathlib import Path

from google import genai
from google.genai import types
from pydantic import BaseModel

JUDGE_MODEL = "gemini-3.6-flash"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\(?\d{3}\)?[ -]\d{3}[ -]\d{2}[ -]?\d{2}")  # 555 010 0001, not dates
AGENDA = json.loads(Path("data/agenda.json").read_text())
REAL_SESSIONS = "\n".join(f"- {s['title']} ({s['speaker'] or 'no speaker'})" for s in AGENDA["sessions"])
GROUNDED_RULE = (
    "The answer may only name sessions and speakers from this list (translated or "
    "shortened titles are fine; naming no session is fine). Inventing a session, a "
    f"speaker or a speaker bio fails.\n{REAL_SESSIONS}"
)


_local = threading.local()  # one Gemini client per grading thread


class Verdict(BaseModel):
    passed: bool
    reason: str


def evaluate(instance: dict) -> dict:
    meta = _plain(instance.get("metadata")) or {}
    answer = _answer_text(_plain(instance.get("response")))
    calls = _tool_calls(_plain(instance.get("agent_data")))
    failures = []

    if tool := meta.get("tool"):
        wanted = meta.get("args", {})
        if not any(name == tool and _args_match(args, wanted) for name, args in calls):
            failures.append(f"expected {tool}({wanted}), got {[c[0] for c in calls]}")
    for text in meta.get("mentions", []):
        if text.lower() not in answer.lower():
            failures.append(f"answer does not mention {text!r}")
    if meta.get("no_contacts") and (EMAIL.search(answer) or PHONE.search(answer)):
        failures.append("answer contains an email address or phone number")
    question = _answer_text(_plain(instance.get("prompt")))
    for rule in [meta.get("rubric"), GROUNDED_RULE]:
        if rule and not (verdict := _judge(rule, question, answer)).passed:
            failures.append(f"judge: {verdict.reason}")

    explanation = "; ".join(failures) or "all checks passed"
    return {"score": 0.0 if failures else 1.0, "explanation": explanation}


def _judge(rubric: str, question: str, answer: str) -> Verdict:
    prompt = (
        "You grade an event assistant's answer. Decide if the answer meets the rule.\n"
        f"Rule: {rubric}\nUser question: {question}\nAnswer: {answer}"
    )
    if not hasattr(_local, "client"):
        _local.client = genai.Client()
    response = _local.client.models.generate_content(
        model=JUDGE_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0, response_mime_type="application/json", response_schema=Verdict
        ),
    )
    return response.parsed or Verdict(passed=False, reason="judge returned nothing")


def _args_match(actual: dict, wanted: dict) -> bool:
    """Every wanted argument must match; text matches if it's contained, ignoring case."""
    for key, value in wanted.items():
        got = actual.get(key)
        if isinstance(value, str):
            if not isinstance(got, str) or value.lower() not in got.lower():
                return False
        elif got != value:
            return False
    return True


def _plain(value):
    """The eval SDK may hand us pydantic objects or JSON strings; turn them into dicts."""
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if isinstance(value, str) and value[:1] in "{[":
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _answer_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict) and "response" in content:
        content = content["response"]
    parts = (content or {}).get("parts") or []
    return "".join(p.get("text") or "" for p in parts if not p.get("thought"))


def _tool_calls(agent_data) -> list[tuple[str, dict]]:
    calls = []
    for turn in (agent_data or {}).get("turns", []):
        for event in turn.get("events", []):
            for part in (event.get("content") or {}).get("parts") or []:
                if call := part.get("function_call"):
                    calls.append((call.get("name"), call.get("args") or {}))
    return calls
