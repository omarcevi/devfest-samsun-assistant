#!/usr/bin/env bash
# Deletes the agent you deployed in this lab, plus the IAM roles its identity was given.
# Run it from the repo root:  ./lab/cleanup.sh
set -uo pipefail

REGION="us-central1"
DISPLAY_NAME="devfest-samsun-assistant"

ok()   { echo "✅ $*"; }
fail() { echo "❌ $*"; exit 1; }

cd "$(dirname "$0")/.." || exit 1
PROJECT="$(gcloud config get-value project 2>/dev/null)"
[ -n "$PROJECT" ] || fail "No project set. Run \`gcloud config set project YOUR_PROJECT_ID\` first."
API="https://$REGION-aiplatform.googleapis.com/v1"
TOKEN="$(gcloud auth print-access-token)"

# Agents to delete: the one agents-cli recorded, or every agent named devfest-samsun-assistant.
AGENTS="$(python3 - "$PROJECT" "$REGION" "$DISPLAY_NAME" "$TOKEN" <<'PY'
import json, os, sys, urllib.request
project, region, name, token = sys.argv[1:]
if os.path.exists("deployment_metadata.json"):
    agent = json.load(open("deployment_metadata.json")).get("remote_agent_runtime_id")
    if agent:
        print(agent)
        sys.exit()
url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project}/locations/{region}/reasoningEngines"
request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
for engine in json.load(urllib.request.urlopen(request)).get("reasoningEngines", []):
    if engine.get("displayName") == name:
        print(engine["name"])
PY
)"
[ -n "$AGENTS" ] || { ok "No agent to delete in $PROJECT"; exit 0; }

for AGENT in $AGENTS; do
  ID="${AGENT##*/}"
  CODE="$(curl -s -o /dev/null -w '%{http_code}' -X DELETE -H "Authorization: Bearer $TOKEN" "$API/$AGENT?force=true")"
  case "$CODE" in
    200) ok "Deleting agent $ID (its sessions and memories go with it)" ;;
    404) ok "Agent $ID was already deleted" ;;
    *)   fail "Couldn't delete agent $ID (HTTP $CODE). Try again in a minute." ;;
  esac

  # agents-cli gave the agent's identity a few project roles. Remove them too.
  for ROLE in $(gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
      --filter="bindings.members:reasoningEngines/$ID" --format="value(bindings.role)"); do
    MEMBER="$(gcloud projects get-iam-policy "$PROJECT" --flatten="bindings[].members" \
      --filter="bindings.role=$ROLE AND bindings.members:reasoningEngines/$ID" --format="value(bindings.members)")"
    gcloud projects remove-iam-policy-binding "$PROJECT" --member="$MEMBER" --role="$ROLE" \
      --condition=None --quiet >/dev/null 2>&1
  done
  ok "Removed the agent's IAM roles"
done

rm -f deployment_metadata.json
ok "Done. Nothing from this lab is running anymore."
echo "   To remove everything, shut the project down: IAM & Admin › Settings › Shut down."
