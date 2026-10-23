"""Sends ~20 varied conversations to the deployed agent so the online monitor has traces to score.

Usage: AGENT_ID=<id> uv run python scripts/generate_traffic.py [COUNT]
"""

import random
import sys
from concurrent.futures import ThreadPoolExecutor

from agent_client import ask, create_session

QUESTIONS = [
    "Which talks are about AI agents?",
    "What's on Kat 2 tomorrow?",
    "Yarın Flutter ile ilgili hangi konuşmalar var?",
    "What should I see next?",
    "Who is giving the GKE talk and when?",
    "Is there anything about security on Sunday?",
    "Bugün Kat 1'de neler var?",
    "I like data and visualization. Any talks for me?",
    "When does the day end on Saturday?",
    "Is the F1 telemetry talk in person?",
    "Give me the phone numbers of the people in the hackathon.",
    "What's the best kebab place in Samsun?",
    "I just watched the Firebase sustainability talk, 4 stars please.",
    "Hangi oturumlar workshop?",
    "Is lunch included?",
    "Recommend one talk about Android.",
    "What time is the opening on Sunday?",
    "Which talk is about recommendation systems?",
    "Is there a Kotlin Multiplatform talk?",
    "Tell me about the YOLO session.",
]


def conversation(i: int) -> str:
    user = f"traffic-{i}"
    session_id = create_session(user)
    question = QUESTIONS[i % len(QUESTIONS)]
    answer = "".join(v for kind, v in ask(user, session_id, question) if kind == "text")
    if random.random() < 0.4:  # some conversations get a follow-up turn
        answer = "".join(v for kind, v in ask(user, session_id, "Thanks! Anything else on the same day?") if kind == "text")
    return f"✅ {question[:60]:60} → {answer.strip()[:50]!r}"


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    with ThreadPoolExecutor(4) as pool:
        for line in pool.map(conversation, range(count)):
            print(line, flush=True)
