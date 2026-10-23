"""Asks the local agent one question (no server) and prints the tool calls and the answer."""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv(".env")

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from app.agent import app  # noqa: E402


async def main(question: str) -> None:
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name="app", user_id="local")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    print(f"\033[36m👤 {question}\033[0m")
    async for event in runner.run_async(user_id="local", session_id=session.id, new_message=message):
        for part in event.content.parts if event.content else []:
            if part.function_call:
                print(f"\033[2m   🔧 {part.function_call.name}({dict(part.function_call.args or {})})\033[0m")
            elif part.text and not part.thought:
                print(f"🤖 {part.text.strip()}")


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "Which talks are about AI agents?"))
