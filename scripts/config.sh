# Shared settings for the stage scripts. Override any of them with environment variables.
# shellcheck disable=SC2034  # these are read by the scripts that source this file
PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"
# The pre-deployed v2 instance: memories seeded for "ayse", used by the public chat page.
BACKUP_AGENT_ID="${BACKUP_AGENT_ID:-2923887566157512704}"
AGENT_ID="${AGENT_ID:-$BACKUP_AGENT_ID}"
MCP_SERVICE="samsun-attendees-mcp"
PROXY_SERVICE="samsun-chat-proxy"
DEMO_NOW_FOR_EVALS="2026-10-24T14:00:00+03:00"
export GOOGLE_CLOUD_PROJECT="$PROJECT" AGENT_ID

BOLD=$'\033[1m'; DIM=$'\033[2m'; GREEN=$'\033[32m'; RED=$'\033[31m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
say() { printf '\n%s%s%s\n' "$BOLD" "$*" "$RESET"; }
