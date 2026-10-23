"""Morning-of-the-talk check: one ✅/❌ line per thing the demos need."""

import json
import os
import subprocess
import time
from pathlib import Path

import requests
from agent_client import ask, create_session, memories, project

results = []


def check(name: str, fn) -> None:
    started = time.time()
    try:
        detail = fn() or ""
        ok = True
    except Exception as error:  # every failure becomes one ❌ line
        detail, ok = str(error).splitlines()[0][:110], False
    results.append(ok)
    print(f"{'✅' if ok else '❌'}  {name:34} {detail}  \033[2m({time.time() - started:.0f}s)\033[0m", flush=True)


def run(*cmd: str) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if out.returncode:
        raise RuntimeError((out.stderr or out.stdout).strip() or f"{cmd[0]} failed")
    return out.stdout.strip()


def gcloud_auth():
    run("gcloud", "auth", "print-access-token")
    run("gcloud", "auth", "application-default", "print-access-token")
    return "gcloud + application-default"


def billing():
    info = json.loads(run("gcloud", "billing", "projects", "describe", project(), "--format=json"))
    assert info.get("billingEnabled"), "billing is not enabled"
    return project()


def agent_answers():
    session_id = create_session("morning-check")
    answer = "".join(v for kind, v in ask("morning-check", session_id, "Which talks are on Kat 2 on Sunday?") if kind == "text")
    assert "Kat 2" in answer, f"unexpected answer: {answer[:80]}"
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/check_session.txt").write_text(session_id)
    return f"agent {os.environ['AGENT_ID']}"


def ayse_memories():
    facts = memories("ayse")
    assert facts, "no memories for ayse: run ./scripts/demo3_memory.sh seed"
    return facts[0][:70]


def trace_link():
    session_id = Path("artifacts/check_session.txt").read_text().strip()
    out = run("uv", "run", "python", "scripts/trace_link.py", session_id)
    return "trace found for the check request" if "console.cloud.google.com/traces" in out else out[-80:]


def proxy():
    url = run("gcloud", "run", "services", "describe", "samsun-chat-proxy", "--region", "us-central1",
              "--format=value(status.url)")
    status = requests.get(f"{url}/api/status", timeout=20).json()
    return "CHAT_ENABLED=true" if status["enabled"] else "⚠️ CHAT_ENABLED=false (demo ended page)"


def contacts_blocked():
    policy = run("gcloud", "run", "services", "get-iam-policy", "samsun-attendees-mcp", "--region", "us-central1",
                 "--format=json")
    assert "agents.global" not in policy, "an agent identity has run.invoker on the attendees MCP server!"
    return "no agent may invoke samsun-attendees-mcp"


def evals():
    env = {**os.environ, "DEMO_NOW": "2026-10-24T14:00:00+03:00"}
    subprocess.run(["agents-cli", "eval", "run", "--dataset", "evals/time_awareness.json", "--config",
                    "evals/eval_config.yaml", "--output", "artifacts/eval_check"],
                   capture_output=True, env=env, timeout=300)
    out = run("uv", "run", "python", "evals/summary.py", "artifacts/eval_check")
    return out.splitlines()[-1].strip()


def agenda():
    data = json.loads(Path("data/agenda.json").read_text())
    return f"read on {data['read_on']}: re-read {data['source'][:45]}..."


if __name__ == "__main__":
    print(f"\n\033[1mMorning check   project={project()}   agent={os.environ.get('AGENT_ID')}\033[0m\n")
    check("gcloud auth", gcloud_auth)
    check("project + billing", billing)
    check("deployed agent answers", agent_answers)
    check("memories for ayse", ayse_memories)
    check("trace link", trace_link)
    check("time_awareness eval passes", evals)
    check("public chat proxy", proxy)
    check("attendee contacts blocked", contacts_blocked)
    check("agenda", agenda)
    print(f"\n{'✅ All good.' if all(results) else '❌ Fix the lines above, or switch to the backup plan.'}\n")
