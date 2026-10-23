"""DevFest Samsun 2026 Assistant: one agent, a few tools and long-term memory."""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.attendees import attendee_tools
from app.memory import PreloadMemoryTool, save_to_memory
from app.tools import get_current_time, get_session, search_sessions, submit_feedback

root_agent = Agent(
    name="samsun_assistant",
    model=Gemini(model="gemini-3.6-flash", retry_options=types.HttpRetryOptions(attempts=3)),
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
