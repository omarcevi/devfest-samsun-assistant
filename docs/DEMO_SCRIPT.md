# Stage runbook: The Google Cloud Stack for Production AI Agents

DevFest Samsun 2026 · Saturday Oct 24 · 10:30–11:10 · Kat 1

All commands run from the repo root on your laptop, in `cloud-agents-project`. Timings were measured on Oct 23–24.

| Thing | Value |
|---|---|
| Backup / public agent | `samsun-assistant-backup`, id **2923887566157512704** (min 1 instance, so no cold start) |
| Its console page | https://console.cloud.google.com/agent-platform/runtimes/locations/us-central1/agent-engines/2923887566157512704/dashboard?project=cloud-agents-project |
| Stage deploy | `devfest-samsun-assistant` (created live, same as the participants') |
| Public chat page | https://omarcevi.dev/demos/devfest-samsun-agent → proxy `samsun-chat-proxy` |
| Lab guide | https://omarcevi.dev/workshops/devfest-samsun-agent |
| Attendees MCP (blocked) | Cloud Run `samsun-attendees-mcp`, IAM-only |
| Online monitor | `samsun-quality` on the backup |

The scripts default to the backup (`AGENT_ID=2923887566157512704`, set in `scripts/config.sh`). To point them at another agent, prefix `AGENT_ID=<id>`.

## Before the talk (09:30)

1. `gcloud auth login` and `gcloud auth application-default login` if either has expired, then `gcloud config set project cloud-agents-project`.
2. `./scripts/check.sh`. Every line should be ✅. It takes about 1.5 minutes.
3. Re-read the agenda: https://kommunity.com/gdg-samsun/events/devfest-samsun-2026-1057d7ef. If anything changed, see **Agenda changes** below.
4. Open these tabs:
   - the backup's console page, on Playground
   - Trace explorer
   - Evaluation › Online monitors
   - the public chat page on your phone
5. Terminal font size: big. Run `clear` before each demo.

## Demo 1, "Agent in 15 lines" (the participants' Step 3)

- **Participants:** they run `uv run adk web --port 8080 --allow_origins "*"` in Cloud Shell.
- **You (fallback, if Wi-Fi or Cloud Shell fails):** `./scripts/demo1_local.sh` (~15 s), or `./scripts/demo1_local.sh web` for the dev UI on http://localhost:8080.
- **Say:**
  - "One model, one instruction, plain Python functions as tools."
  - "The model picks a tool, reads the result, answers."
- **Expect:** 🔧 `get_current_time`, 🔧 `search_sessions`, …, then three AI-agent talks with speaker, day, time and floor.
- **If it fails:** `docs/screenshots/01-local.png`.

## Demo 2, "Run": deploy alongside the room

```bash
./scripts/demo2_deploy.sh          # agents-cli deploy --agent-identity --no-wait --project cloud-agents-project
```

- **Expect:** "Deployment Parameters…", `🔧 Creating agent identity`, `🔐 Granting IAM roles to: principal://agents.global.proj-666312056831…`, then it returns.
- **Measured time:**
  - first deploy, fresh project: **5 min 07 s**
  - update of an existing agent: 3–4 min
- **Say:**
  - "--agent-identity gives the agent its own principal in IAM. No shared service account."
  - "While it builds, let's look at one I deployed earlier."
- **Later:** `./scripts/demo2_deploy.sh status` should end with `✅ Deployment successful!`.
- **Participants:** they run `agents-cli deploy --agent-identity -i` and press Enter at `Proceed? [Y/n]`.
- **If it fails:** stay on the backup and show `docs/screenshots/02-deploy.png`.

## Demo 3, "Remember" (backup instance, ~30 s)

```bash
./scripts/demo3_memory.sh          # session 2 for user ayse + the memories Memory Bank stored
```

- **Say:**
  - "Yesterday, in another session, Ayşe told it she likes ML and Flutter. New session, same user, no context: 'What should I see tomorrow?'"
- **Expect:** `get_current_time`, `search_sessions`, then three Sunday picks:
  - **From Model to Cluster** (GKE AI/ML) 10:30 Kat 1
  - **Bağlantıyı Kurmak: Modern Flutter & Firebase** 14:15 Kat 2
  - **No GPU Left Behind** (YOLO) 15:30 Kat 1

  Then `🧠 What Memory Bank stored for ayse: • I am interested in machine learning (ML) and Flutter.`
- **Full version** with session 1: `./scripts/demo3_memory.sh full` (~55 s; Memory Bank needs ~20–30 s to extract).
- **The code behind it:** `PreloadMemoryTool()` + `after_agent_callback=save_to_memory` (see `docs/SLIDE_SNIPPETS.md` §3).
- **If it fails:** run the same two questions in the backup's console Playground (memory works across "New Session" there), or show `03-memory-1.png`, `03-memory-2.png` and `04-memories.png`.

## Demo 4, "Control": shown as screenshots

- **Path used: plain IAM, not Agent Gateway.**
  - The attendees MCP server is on Cloud Run with `--no-allow-unauthenticated`, and no agent identity has `roles/run.invoker`.
  - The agent's code calls it with its own Agent Identity token; Cloud Run says no.
  - Slide wording: "**IAM** blocks it" (not "the gateway blocks it").
- **Screenshots:**
  - `05-control-reply.png`: agent reply
  - `06-control-log.png`: Cloud Run log `403 … The IAM principal lacks {run.routes.invoke} permission`
- **Live version if you want it (~30 s):** `./scripts/fallback_gateway.sh`.
- **Say:**
  - "The prompt doesn't forbid it. The tool is wired in. The platform decides what the agent may touch."
- **Agent Gateway:** it's GA and available in us-central1, but it isn't set up here. Every agent in a project and region must share one egress gateway, and the backup is serving the public page. Details are in `docs/VERIFIED.md`.

## Demo 5, "Observe" (~10 s)

```bash
./scripts/demo4_trace.sh           # trace of the demo 3 request
```

- **Expect:** a terminal waterfall, then a 👉 Trace explorer link (cmd-click it):

  ```text
  invoke_agent samsun_assistant  10.3s
  retrieve_memories               0.5s
  generate_content gemini-3.6-flash
  execute_tool get_current_time
  execute_tool search_sessions
  generate_content …
  save_memories
  ```

- **Say:**
  - "Every model call and tool call is a span. This is the request we just made."
- **Note:** the agent page's own **Traces** tab stayed empty tonight. Use the Trace explorer link the script prints.
- **If it fails** ("No trace yet"): wait 10 s and rerun, or show `07-trace.png`.

## Demo 6, "Evaluate" (~35 s per run)

```bash
./scripts/demo5_eval.sh v1-bug     # ❌ time_awareness: recommends your 10:30 talk at 14:00
./scripts/demo5_eval.sh v2-fixed   # ✅ time_awareness
```

- **Say:**
  - "It's 14:00 on Saturday. v1 has no clock, so it happily recommends my own talk, which ended at 11:10."
  - "One eval case catches it. The fix is a tool and one instruction line."
- **Expect for v1:** `❌ time_awareness ← judge: The answer recommended two sessions (at 10:30 and 11:30) that occurred before … 14:00`.
- **Full set (10 cases, ~45 s):** `./scripts/demo5_eval.sh full` gives `10/10 passed`.
- **Online monitor:** Evaluation › Online monitors › **samsun-quality** › View traces. It runs every 10 min on the backup's traffic, including the public page.
- **If it fails:** `08-eval-fail.png`, `09-eval-pass.png`, `10-online-monitor.png`.

## Public page

### Is it up?

```bash
curl -s https://samsun-chat-proxy-666312056831.us-central1.run.app/api/status
```

Expect `{"enabled":true,...}`. Then open the page on a phone and tap a chip.

### Kill switch (flip it Sunday evening)

```bash
gcloud run services update samsun-chat-proxy --region us-central1 --update-env-vars CHAT_ENABLED=false
```

The page then shows "The DevFest Samsun demo has ended. The code is on GitHub." Set it back to `true` to undo.

### Point it at a different agent

```bash
gcloud run services update samsun-chat-proxy --region us-central1 --update-env-vars AGENT_ID=<id>
# the proxy's service account needs the custom role on that agent:
ENGINE=projects/cloud-agents-project/locations/us-central1/reasoningEngines/<id>
curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://us-central1-aiplatform.googleapis.com/v1/${ENGINE}:setIamPolicy" \
  -d '{"policy":{"bindings":[{"role":"projects/cloud-agents-project/roles/samsunAgentCaller","members":["serviceAccount:samsun-chat-proxy@cloud-agents-project.iam.gserviceaccount.com"]}]}}'
```

### Limits

All are env vars on the proxy (`gcloud run services update … --update-env-vars NAME=value`):

| Limit | Value |
|---|---|
| Message length | 500 characters |
| Turns per chat | 20 |
| Per user | 6/min and 60/day |
| Per IP | 60/min (venue Wi-Fi is one IP) |
| Global | 80/min, 4000/day |

The proxy runs on **one instance** (`max-instances=1`, concurrency 300), so these in-memory limits are exact.

> ⚠️ Agent Runtime quota: "Query Reasoning Engine requests" = **30/min/project/region** in this project. See the load-test notes below.

### After the event

```bash
./scripts/teardown.sh memories    # deletes the public users' memories (user ids web-…)
```

## Agenda changes (≤ 10 minutes)

1. Edit `data/agenda.json`: keep titles and names exactly as on kommunity.com, and update `read_on`.
2. Run `uv run pytest tests/unit -q`. The agenda-rules test catches format/tag mistakes.
3. `git commit -am "Agenda: …" && git push`. Participants who clone after this get the new agenda.
4. Redeploy the backup:

   ```bash
   git worktree add /tmp/backup main && cp .env /tmp/backup/ && cd /tmp/backup && agents-cli deploy --agent-identity --service-name samsun-assistant-backup --no-confirm-project --min-instances 1 --max-instances 20 --concurrency 16 --env-vars "ATTENDEES_MCP_URL=https://samsun-attendees-mcp-666312056831.us-central1.run.app,OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY"
   ```

   Measured 3:00–3:45. The page keeps working during the update.
5. Copy `data/agenda.json` to `omarcevi.github.io/demos/devfest-samsun-agent/agenda.json` (the "Today's agenda" panel) and push.

## If the Wi-Fi dies

- Screenshots: `docs/screenshots/01-…` to `11-…`, in demo order.
- Terminal recordings: `docs/recordings/` (demos 1, 3, 5). Play with `asciinema play docs/recordings/demo3.cast`.
- Phone hotspot: the scripts need about 1 MB per demo.
