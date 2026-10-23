# Slide snippets

Copied from the final code on `main` (= `v2-fixed`). Each block is ≤ 15 lines where possible; `...` marks a trim.

## 1. `app/agent.py` (whole file, 30 lines)

```python
from google.adk.agents import Agent
from google.adk.apps import App
from google.genai import types

from app.attendees import attendee_tools
from app.memory import PreloadMemoryTool, save_to_memory
from app.tools import get_current_time, get_session, search_sessions, submit_feedback

root_agent = Agent(
    name="samsun_assistant",
    model="gemini-3.6-flash",
    # A stalled Gemini call is cut off after 40 s and retried (3 tries in total).
    generate_content_config=types.GenerateContentConfig(http_options=types.HttpOptions(
        timeout=40_000, retry_options=types.HttpRetryOptions(attempts=3))),
    instruction="""You help attendees of DevFest Samsun 2026 (Saturday 2026-10-24 and Sunday 2026-10-25).
Only recommend sessions that your tools return. Never invent sessions or speaker bios.
Suggest at most 3 sessions. For each, give the speaker, day, time and floor (Kat 1 or Kat 2).
Call get_current_time first and never recommend sessions that already ended.
Use what you remember about the user to personalize picks without asking again.
Reply in the user's language, short and friendly. Keep session titles exactly as written.
If the agenda doesn't cover a question, point to https://kommunity.com/gdg-samsun/events/devfest-samsun-2026-1057d7ef
If a question isn't about DevFest, politely steer back to the event.""",
    tools=[search_sessions, get_session, submit_feedback, get_current_time,
           PreloadMemoryTool(), *attendee_tools],
    after_agent_callback=save_to_memory,
)

app = App(name="app", root_agent=root_agent)
```

### 1b. Trimmed to 15 lines for the "Agent in 15 lines" slide (imports, timeout and the optional MCP tool left out)

```python
root_agent = Agent(
    name="samsun_assistant",
    model="gemini-3.6-flash",
    instruction="""You help attendees of DevFest Samsun 2026 ...
Only recommend sessions that your tools return.
Suggest at most 3 sessions. For each, give the speaker, day, time and floor.
Call get_current_time first and never recommend sessions that already ended.
Reply in the user's language, short and friendly. ...""",
    tools=[search_sessions, get_session, submit_feedback, get_current_time,
           PreloadMemoryTool()],
    after_agent_callback=save_to_memory,
)

app = App(name="app", root_agent=root_agent)
```

## 2. `search_sessions` (whole, `app/tools.py`)

```python
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
```

## 3. Memory: retrieve before each answer, save after it

```python
# app/agent.py
root_agent = Agent(
    ...
    tools=[..., PreloadMemoryTool()],        # Memory Bank → prompt, before each model call
    after_agent_callback=save_to_memory,     # conversation → Memory Bank, after each answer
)

# app/memory.py
async def save_to_memory(callback_context: CallbackContext) -> None:
    """Runs after the agent answers. Memory Bank generates memories in the background."""
    await callback_context.add_session_to_memory()
```

No setup: on Agent Runtime the template wires in Memory Bank (`VertexAiMemoryBankService`); locally it's in-memory. (`app/memory.py` also wraps both steps in a trace span; that's left off the slide.)

## 4. Deploy

```bash
agents-cli deploy --agent-identity -i
```

On stage, so it returns right away:

```bash
agents-cli deploy --agent-identity --no-wait --project cloud-agents-project
agents-cli deploy --status
```

`-i` is needed in agents-cli 1.11.0 to get the "Deploying to project X. Proceed? [Y/n]" prompt; without `-i`, `--project` or `--no-confirm-project` the command stops with "confirmation required".

## 5. The eval case that catches the bug (`evals/dataset.json`)

```json
{
  "eval_case_id": "time_awareness",
  "prompt": {"role": "user", "parts": [{"text":
    "It's Saturday and I'm at DevFest. I'm into AI agents. What should I see today?"}]},
  "metadata": {
    "rubric": "It is now 14:00 on Saturday 2026-10-24. FAIL if the answer recommends
               any session that already ended (anything before 14:00 that Saturday).
               Saying a session has already ended is fine."
  }
}
```

Run it with the clock pinned:

```bash
DEMO_NOW=2026-10-24T14:00:00+03:00 agents-cli eval run \
  --dataset evals/time_awareness.json --config evals/eval_config.yaml
```

Result: `v1-bug` ❌ (recommends the 10:30 and 11:30 talks), `v2-fixed` ✅.

## 6. The fix: `get_current_time` (`app/tools.py`)

```python
def get_current_time() -> str:
    """Returns the current day, date and time at DevFest Samsun (Europe/Istanbul)."""
    # DEMO_NOW pins the clock for a reproducible demo, e.g. 2026-10-24T14:00:00+03:00
    demo_now = os.environ.get("DEMO_NOW")
    now = datetime.fromisoformat(demo_now) if demo_now else datetime.now(ZoneInfo("Europe/Istanbul"))
    return now.strftime("%A %Y-%m-%d %H:%M")
```

…plus one instruction line: `Call get_current_time first and never recommend sessions that already ended.`

## 7. Control: why the contact lookup fails

```bash
# The MCP server only accepts callers that IAM allows. No agent is on the list.
gcloud run deploy samsun-attendees-mcp --source mcp/attendees --no-allow-unauthenticated

# Cloud Run's log for every call the agent makes:
# 403  The IAM principal lacks {run.routes.invoke} permission.
```

The prompt doesn't forbid it, and the code is wired to the tool. IAM is what blocks it.
