"""Demo 3, Remember: two separate sessions for the same user, then the memories Memory Bank stored.

    AGENT_ID=<backup id> uv run python scripts/demo3_memory.py            # both sessions
    AGENT_ID=<backup id> uv run python scripts/demo3_memory.py --seed     # session 1 only (seed the backup)
    AGENT_ID=<backup id> uv run python scripts/demo3_memory.py --recall   # session 2 + memories only
"""

import sys
import time
from pathlib import Path

from agent_client import ask, create_session, memories

USER = "ayse"
FIRST = "Hi! First DevFest for me. I'm into ML and Flutter."
SECOND = "What should I see tomorrow?"
BOLD, DIM, CYAN, GREEN, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[32m", "\033[0m"


def chat(title: str, message: str) -> str:
    print(f"\n{BOLD}{title}{RESET}  {DIM}(user: {USER}, new session){RESET}")
    print(f"{CYAN}👤 {message}{RESET}")
    session_id = create_session(USER)
    answer = ""
    for kind, value in ask(USER, session_id, message):
        if kind == "tool":
            print(f"{DIM}   🔧 {value}{RESET}")
        else:
            answer += value
    print(f"🤖 {answer.strip()}\n")
    return session_id


def wait_for_memories(timeout: int = 45) -> list[str]:
    print(f"{DIM}⏳ Memory Bank is extracting facts in the background...{RESET}", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        facts = memories(USER)
        if any("flutter" in f.lower() or "ml" in f.lower() or "machine" in f.lower() for f in facts):
            return facts
        time.sleep(3)
    return memories(USER)


def show_memories(facts: list[str]) -> None:
    print(f"\n{BOLD}🧠 What Memory Bank stored for {USER}:{RESET}")
    for fact in facts or ["(nothing yet: try again in a few seconds)"]:
        print(f"{GREEN}   • {fact}{RESET}")
    print()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "--recall":
        chat("Session 1", FIRST)
        facts = wait_for_memories()
        if mode == "--seed":
            show_memories(facts)
            sys.exit(0)
    session_id = chat("Session 2", SECOND)
    show_memories(memories(USER))
    # demo4_trace.sh opens the trace of this request.
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/last_session.txt").write_text(session_id)
