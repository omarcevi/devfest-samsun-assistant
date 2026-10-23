#!/usr/bin/env bash
# Removes what the demos created. Read each mode before you run it.
#   ./scripts/teardown.sh memories   after the event: delete the public page users' memories (keeps everything else)
#   ./scripts/teardown.sh stage      delete the agent deployed live on stage (devfest-samsun-assistant)
#   ./scripts/teardown.sh all        everything: both agents, Cloud Run services, proxy identity, IAM, monitor
# Don't run "all" before the talk: it deletes the backup instance.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh
API="https://$REGION-aiplatform.googleapis.com"
TOKEN="$(gcloud auth print-access-token)"

delete_agent() {  # $1 = agent id
  local engine="projects/$PROJECT/locations/$REGION/reasoningEngines/$1"
  curl -s -o /dev/null -w "   delete agent $1: HTTP %{http_code}\n" -X DELETE \
    -H "Authorization: Bearer $TOKEN" "$API/v1/$engine?force=true"
  for role in $(gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
      --filter="bindings.members:reasoningEngines/$1" --format="value(bindings.role)"); do
    member="$(gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
      --filter="bindings.role=$role AND bindings.members:reasoningEngines/$1" --format="value(bindings.members)")"
    gcloud projects remove-iam-policy-binding "$PROJECT" --member="$member" --role="$role" \
      --condition=None --quiet >/dev/null 2>&1 && echo "   removed $role from agent $1"
  done
}

agent_ids_named() {  # $1 = display name
  curl -s -H "Authorization: Bearer $TOKEN" "$API/v1/projects/$PROJECT/locations/$REGION/reasoningEngines" |
    python3 -c "import json,sys; [print(e['name'].split('/')[-1]) for e in json.load(sys.stdin).get('reasoningEngines',[]) if e.get('displayName')=='$1']"
}

case "${1:-}" in
  memories)
    say "Deleting the public page users' memories (user ids starting with web-)"
    uv run python - <<'PY'
import json, sys
sys.path.insert(0, "scripts")
import requests
from agent_client import API, _headers, engine
url, deleted, token = f"{API}/v1beta1/{engine()}/memories", 0, ""
while True:
    page = requests.get(url, headers=_headers(), params={"pageSize": 100, "pageToken": token}, timeout=60).json()
    for memory in page.get("memories", []):
        if memory.get("scope", {}).get("user_id", "").startswith("web-"):
            requests.delete(f"{API}/v1beta1/{memory['name']}", headers=_headers(), timeout=60)
            deleted += 1
    token = page.get("nextPageToken")
    if not token:
        break
print(f"   deleted {deleted} memories")
PY
    ;;
  stage)
    say "Deleting the stage agent (devfest-samsun-assistant)"
    for id in $(agent_ids_named devfest-samsun-assistant); do delete_agent "$id"; done
    rm -f deployment_metadata.json
    ;;
  all)
    say "Deleting EVERYTHING the demos created in $PROJECT"
    for id in $(agent_ids_named devfest-samsun-assistant) $(agent_ids_named samsun-assistant-backup); do delete_agent "$id"; done
    for service in "$PROXY_SERVICE" "$MCP_SERVICE"; do
      gcloud run services delete "$service" --region "$REGION" --project "$PROJECT" --quiet 2>&1 | tail -1
    done
    gcloud iam service-accounts delete "samsun-chat-proxy@$PROJECT.iam.gserviceaccount.com" --project "$PROJECT" --quiet 2>&1 | tail -1
    gcloud iam roles delete samsunAgentCaller --project "$PROJECT" --quiet 2>&1 | tail -1
    echo "   The online monitor goes away with the backup agent. Delete the budget alert in Billing › Budgets if you no longer want it."
    rm -f deployment_metadata.json
    ;;
  *)
    sed -n '2,7p' "$0"; exit 1 ;;
esac
say "Done."
