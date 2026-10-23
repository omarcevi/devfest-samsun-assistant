"""Load test for the public chat proxy: phones that open the page and ask a few questions.

    uvx --from locust==2.47.0 locust -f tests/load_test/locustfile.py --headless \
        -u 100 -r 5 -t 5m --host https://samsun-chat-proxy-666312056831.us-central1.run.app \
        --csv tests/load_test/.results/run

Every request comes from this one machine, like a room on one Wi-Fi IP, so the
per-IP and global limits kick in. "chat 429" in the results means the proxy said
"wait a minute", which is the intended behaviour under overload.
"""

import json
import random
import time
import uuid

from locust import HttpUser, between, events, task

QUESTIONS = [
    "Which talks are about AI agents?",
    "What's on Kat 2 tomorrow?",
    "Yarın Flutter ile ilgili hangi konuşmalar var?",
    "What should I see next?",
    "Who gives the GKE talk?",
    "Is there a security talk on Sunday?",
]


class Attendee(HttpUser):
    wait_time = between(20, 40)  # people read the answer before asking again

    def on_start(self):
        self.user_id = str(uuid.uuid4())
        self.session_id = None

    def new_session(self) -> bool:
        with self.client.post("/api/session", json={"user_id": self.user_id}, name="session",
                              catch_response=True) as response:
            if response.status_code == 200:
                self.session_id = response.json()["session_id"]
                return True
            response.failure(f"session {response.status_code}")
            return False

    @task
    def ask(self):
        if not self.session_id and not self.new_session():
            return
        started = time.time()
        first_text = None
        body = {"user_id": self.user_id, "session_id": self.session_id, "message": random.choice(QUESTIONS)}
        with self.client.post("/api/chat", json=body, stream=True, name="chat",
                              catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"chat {response.status_code}")
                return
            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                event = json.loads(line[5:])
                if event["type"] == "text" and first_text is None:
                    first_text = time.time() - started
                if event["type"] == "error":
                    response.failure(f"stream error {event.get('code')}")
                    return
            response.success()
        total = time.time() - started
        events.request.fire(request_type="SSE", name="time to first text", response_time=(first_text or total) * 1000,
                            response_length=0, exception=None, context={})
        events.request.fire(request_type="SSE", name="full answer", response_time=total * 1000,
                            response_length=0, exception=None, context={})
