# What was verified, and how

Everything here was run tonight (Oct 23–24, 2026) against `cloud-agents-project` (demo) or a brand-new org-less project `devfest-lab-test-19699` (lab), unless marked otherwise.

## Versions

| Tool | Version | Where |
|---|---|---|
| agents-cli (`google-agents-cli`) | **1.11.0** (latest on PyPI) | laptop and Cloud Shell (`lab/setup.sh` pins it) |
| agents-cli built into Cloud Shell | 1.3.1 in `/usr/local/bin` | why the guide has `source ~/.profile` |
| google-adk | **2.12.0** (pinned in `pyproject.toml`, `uv.lock`) | 2.13.0 exists; not tested |
| google-cloud-agentplatform | 2.5.0 | |
| google-genai | 2.31.0 | |
| google-auth | 2.62.0 | needed for `bind_id_token=False` |
| mcp (client) | 2.3.0 | agent side |
| fastmcp | 4.1.3 | `mcp/attendees` server |
| gcloud | 590.0.0 | |
| uv | 0.12.2 | preinstalled in Cloud Shell |
| Python | 3.12 | Cloud Shell has 3.12.3 |

## Model and region

- **Model: `gemini-3.6-flash`.** Listed in `global` and `us-central1`. On Oct 23 at 22:00, `gemini-3.8-flash` (the scaffold default) answered "say hi" in 35–53 s and then returned `504 DEADLINE_EXCEEDED`. `gemini-3.7-flash` took ~40 s, while `gemini-3.6-flash` took 1.5–4 s.
- **Model location: `global`.** `generate_content` on `us-central1` returned **404 NOT_FOUND** for 3.5–3.8 Flash in this project, even though `models.list` lists them there. `.env` uses `GOOGLE_CLOUD_LOCATION=global`.
- **Agent Runtime region: `us-central1`** (`agents-cli-manifest.yaml`). None of these Flash models are served in `europe-west4`.

## agents-cli

| Command | Result |
|---|---|
| `agents-cli create devfest-samsun-assistant --root-agent-name samsun_assistant -d agent_runtime --region us-central1 --agent-gateway -p -y` | Scaffold: `app/fast_api_app.py`, `app/app_utils/*`, Dockerfile (trusts the Agent Gateway CA), manifest with `agent_gateway: true` and `identity_default: agent_identity` |
| `agents-cli deploy --agent-identity -i` | Prompts `Deploying to Google Cloud project 'X'. Proceed? [Y/n]`. **Without `-i`, `--project` or `--no-confirm-project` it fails** with "confirmation required" (source: `deploy/cmd_deploy.py::_confirm_resolved_project`). |
| Deploy time, fresh project, first deploy | **5 min 07 s** (Cloud Shell, 19:52:01 → 19:57:08 UTC) |
| Deploy time, update of an existing agent | 3:00–3:45 |
| Success line | `✅ Deployment successful!`, then `Agent Runtime ID: …` and `Agent Identity: principal://…` |
| `agents-cli deploy --status` during a normal (not `--no-wait`) deploy | Works: `⏳ Deployment still in progress (1m 30s elapsed)`. The pending operation is stored in `deployment_metadata.json`, and the deploy runs server-side. |
| `agents-cli deploy --no-wait`, `--service-name`, `--min-instances`, `--max-instances`, `--concurrency`, `--env-vars`, `--labels`, `--agent-gateway-egress` | Flags exist (`agents-cli deploy --help`). All except `--agent-gateway-egress` were used tonight. |
| `agents-cli eval run --dataset … --config … --output …` | Used for the evals: local custom metric (`evals/checks.py`). The eval instance includes the case's `metadata`. |
| `agents-cli run "…"` | **Hung** (read timeout after 2.5 min) on the laptop. I didn't debug it; `scripts/ask_local.py` replaces it for demo 1. |
| `agents-cli` delete command | **None exists.** `lab/cleanup.sh` and `scripts/teardown.sh` call `DELETE …/reasoningEngines/ID?force=true`. |
| Env vars set by deploy | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` (tracing on by default), `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`, `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`. The project `.env` is the base layer, and `GOOGLE_CLOUD_PROJECT` is dropped as reserved. |
| Roles granted to the agent identity | `roles/aiplatform.user`, `serviceusage.serviceUsageConsumer`, `browser`, `cloudapiregistry.viewer`, `logging.logWriter`, `monitoring.metricWriter`. The platform adds `roles/aiplatform.agentDefaultAccess` for the project principalSet. |

## Agent Identity

- Works on a project **without an organization**. The principal is `principal://agents.global.proj-356328465451.system.id.goog/resources/aiplatform/projects/356328465451/locations/us-central1/reasoningEngines/2875473870163279872`.
- Principal set for all agents in a project: `principalSet://agents.global.proj-PROJECT_NUMBER.system.id.goog/attribute.platformContainer/aiplatform/projects/PROJECT_NUMBER` ([docs](https://docs.cloud.google.com/iam/docs/auth-agent-own-identity)).
- **Calling Cloud Run as the agent:** Agent Identity ID tokens are certificate-bound by default. A plain `*.run.app` URL rejects them with **401** "access token could not be verified". `id_token.fetch_id_token(..., bind_id_token=False)` fixes that (google-auth ≥ 2.62.0). After the fix, Cloud Run logs **403** "The IAM principal lacks {run.routes.invoke} permission" ([docs](https://docs.cloud.google.com/iam/docs/auth-agent-own-identity-external)).
- **Not verified:** that granting `roles/run.invoker` to the agent principal makes the call succeed. I tested a 20-second window and it was still 403. That's probably IAM propagation, and the codelab says Cloud Run only trusts Google-signed tokens. It doesn't affect the demo, which only needs the deny.

## Memory Bank

- **Default on deploy (verified in source).**
  - `get_fast_api_app` auto-configures `agentengine://$GOOGLE_CLOUD_AGENT_ENGINE_ID`.
  - `AdkApp.set_up` uses `VertexAiMemoryBankService` when `GOOGLE_CLOUD_AGENT_ENGINE_ID` is set.
  - `app/app_utils/services.py` now builds it explicitly with the runtime-injected `GOOGLE_CLOUD_AGENT_ENGINE_LOCATION`, so both paths share one service.
- **In ADK 2.12:**
  - `PreloadMemoryTool` lives in `google.adk.tools.preload_memory_tool`; `google.adk.tools` only exports the `preload_memory` instance.
  - `CallbackContext.add_session_to_memory()` and `add_events_to_memory(events=…)` both exist.
- **Live results:**
  - user `ayse` session 1 → Memory Bank stored "I am interested in machine learning (ML) and Flutter." within ~30 s
  - a new session then got ML/Flutter picks without asking
  - memory works across **Playground › New Session** in the console; the Playground uses `userId=user`
- **REST:**
  - `POST v1beta1/{engine}/memories:retrieve` with `{"scope":{"app_name":"app","user_id":…}}`
  - `POST v1beta1/{engine}/memories:purge` with `{"filter":"scope.user_id=\"…\"","force":true}`. This works with a custom role holding only `aiplatform.memories.list/retrieve/delete` + `reasoningEngines.get/query`.

## Agent Runtime APIs used by the proxy and scripts

- Create session: `POST v1/{engine}:query` with `{"class_method":"async_create_session","input":{"user_id":…}}`
- Stream: `POST v1/{engine}:streamQuery?alt=sse` with `{"class_method":"async_stream_query","input":{"user_id","session_id","message","run_config":{"streaming_mode":"sse"}}}`. This gives token streaming; text arrives as `partial` events, then a final aggregated event.
- **Least privilege:**
  - There is no predefined "query one agent" role.
  - Custom role `projects/cloud-agents-project/roles/samsunAgentCaller` = `aiplatform.reasoningEngines.get, .query, aiplatform.memories.list, .retrieve, .delete`.
  - It is granted **on the one agent** with `reasoningEngines/ID:setIamPolicy` to `samsun-chat-proxy@cloud-agents-project.iam.gserviceaccount.com`.
- **Quota** (`gcloud alpha services quota list --service=aiplatform.googleapis.com`): **"Query Reasoning Engine requests" = 30/min/project/region** in this project. The research notes said 90; the live value is 30.

## Model reliability

- `gemini-3.6-flash` had occasional multi-minute stalls tonight: one local run took 2 min 55 s, and the integration tests saw one transient model error.
- `app/agent.py` now sets `generate_content_config=GenerateContentConfig(http_options=HttpOptions(timeout=40_000, retry_options=HttpRetryOptions(attempts=3)))`. google-genai retries client-side timeouts (tested).
- The `v1-bug`/`v2-fixed` tags predate this commit. Their diff is still only the clock fix.

## Tracing

- On by default with agents-cli. Spans: `invoke_workflow` → `invoke_agent` → `call_llm`/`generate_content gemini-3.6-flash` → `execute_tool <name>`.
- `retrieve_memories` and `save_memories` are custom spans from `app/memory.py`. ADK doesn't trace `PreloadMemoryTool`.
- Spans carry `gen_ai.conversation.id = <session id>`. The Cloud Trace v1 filter `+gen_ai.conversation.id:<id>` finds them. The API can return empty pages with a `nextPageToken` before the match, so `scripts/trace_link.py` pages through them.
- **Console:**
  - **Trace explorer** (`console.cloud.google.com/traces/explorer`) shows the spans, including on the fresh lab project.
  - The agent page's **Traces** tab stayed **empty** in both projects tonight, although Cloud Trace had the spans.
  - The guide sends participants to Trace explorer.
- Online-monitor env vars `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY` are set on the backup with `--env-vars`.

## Online monitor

- Console only. **Agent Platform › Agents › Evaluation › Online monitors › + New monitor**: (1) agent, name, region, Traces, All traces; (2) default metrics Final Response Quality, Tool Use Quality, Hallucination, Safety; (3) runs every 10 min, sampling %, max samples per job.
- Created: `samsun-quality` on `samsun-assistant-backup`, 100 %, max 50 samples per run. The API is beta-only, with no gcloud command ([research notes](https://docs.cloud.google.com/gemini-enterprise-agent-platform)).

## Console (lab Step 5)

- Path: search **Agent Platform** › left menu **Agents** › **Deployments** (under *Scale*). The agent is **devfest-samsun-assistant**.
- Tabs: Dashboard, Revisions, Traces, Identity*, Topology*, Security*, Sessions, Playground, Memories, Evaluation (*greyed out on a fresh project).
- On a fresh project the Dashboard pops "API is not enabled: apphub.googleapis.com". `lab/setup.sh` now enables App Hub.

## Cloud Shell (lab)

- `adk web` through Web Preview: every JS module returns **403** and the page is blank. `--allow_origins "*"` fixes it, and `--allow_origins "regex:https://.*\.cloudshell\.dev"` also starts. Tested: UI, chat and tool chips work.
- The dropdown shows **`app`**, already selected.
- `uv` and `agents-cli` 1.3.1 are preinstalled. `~/.local/bin` is only on PATH for new shells, hence `source ~/.profile`.
- Cloud Shell's prompt hook syncs `GOOGLE_CLOUD_PROJECT` from `gcloud config` (`/google/devshell/bashrc.google`).
- `lab/setup.sh`:
  - 24 s on the first run here (warm uv cache), 16 s re-run
  - idempotent
  - APIs: aiplatform, cloudtrace, telemetry, logging, cloudresourcemanager, apphub
- `lab/cleanup.sh`: 33 s, idempotent. Afterwards the project has no agents, buckets, Cloud Run or Artifact Registry. The build runs in a Google-managed project, so no staging bucket is created.
- No Gemini 429s on the brand-new project for ~10 messages.

## Agent Gateway (not used tonight)

- **GA since June 18, 2026; us-central1 supported; no allowlist.** `gcloud network-services agent-gateways list --location=us-central1` → `Listed 0 items.`
- Setup is documented in [set-up-agent-gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/set-up-agent-gateway) and [agent-gateway-runtime-deploy](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-gateway-runtime-deploy):
  1. `agent-gateways import` (AGENT_TO_ANYWHERE)
  2. IAP authz extension + authz policy (start in DRY_RUN)
  3. `gcloud agent-registry services create` for the MCP server
  4. `agents-cli deploy --agent-gateway-egress projects/…/agentGateways/…`
  5. grant `iap.egressViaIAP`
  6. allowlist every Google API host the agent calls; otherwise invocations fail with **498**
- Limits that kept it off the backup tonight: **all agents in a project+region must bind to the same egress gateway**, and changing a binding **irreversibly archives revisions**. Semantic governance policies are **Preview**.
- **The demo uses the IAM path** (`scripts/fallback_gateway.sh`): no agent has `roles/run.invoker` on `samsun-attendees-mcp`, every call is denied, and Cloud Run logs it. Slide wording should say "IAM", not "Agent Gateway".

## Doc links

- Agent Runtime + Agent Gateway deploy: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-gateway-runtime-deploy
- Agent Identity: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/agent-identity
- Agent Identity → Cloud Run: https://docs.cloud.google.com/iam/docs/auth-agent-own-identity-external
- Memory Bank IAM conditions: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/memory-bank/iam-conditions
- streamQuery REST: https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/v1beta1/projects.locations.reasoningEngines/streamQuery
- Agent Gateway monitoring: https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/monitor-agent-gateway
- Release notes: https://docs.cloud.google.com/gemini-enterprise-agent-platform/release-notes
