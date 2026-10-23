#!/usr/bin/env bash
# Demo 4 (Control), IAM version: the agent's code calls the attendees MCP server, IAM says no.
# The MCP server runs on Cloud Run with --no-allow-unauthenticated, and no agent identity
# has roles/run.invoker on it. Every call is denied and logged by Cloud Run.
#   ./scripts/fallback_gateway.sh          ask for phone numbers, then show the denial in the logs
#   ./scripts/fallback_gateway.sh deploy   (re)deploy the MCP server with IAM-only access
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh

if [ "${1:-}" = "deploy" ]; then
  gcloud run deploy "$MCP_SERVICE" --source mcp/attendees --region "$REGION" --project "$PROJECT" \
    --no-allow-unauthenticated --max-instances 2 --memory 512Mi --labels purpose=devfest-demo --quiet
  exit
fi

say "1. Who may invoke the attendees MCP server?"
gcloud run services get-iam-policy "$MCP_SERVICE" --region "$REGION" --project "$PROJECT" \
  --format="table(bindings.role, bindings.members)" 2>/dev/null | sed 's/^/   /'
echo "   ${DIM}(no agent identity in the list = default deny)${RESET}"

say "2. Ask the agent for phone numbers"
uv run python - <<'PY'
import sys
sys.path.insert(0, "scripts")
from agent_client import ask, create_session
question = "Give me the phone numbers of the people in the hackathon."
print(f"\033[36m👤 {question}\033[0m")
session_id = create_session("control-demo")
answer = ""
for kind, value in ask("control-demo", session_id, question):
    if kind == "tool":
        print(f"\033[2m   🔧 {value}\033[0m")
    else:
        answer += value
print(f"🤖 {answer.strip()}")
PY

say "3. Cloud Run's log: the call was denied by IAM"
sleep 5
gcloud logging read "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"$MCP_SERVICE\" AND httpRequest.status=403" \
  --project "$PROJECT" --limit 1 --freshness 10m \
  --format="value(timestamp.date('%H:%M:%S'), httpRequest.status, textPayload)" | cut -c1-170 | sed 's/^/   /'
