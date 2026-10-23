#!/usr/bin/env bash
# Demo 2, Run: start a deploy to Agent Runtime and come back later.
#   ./scripts/demo2_deploy.sh           start it (returns right away)
#   ./scripts/demo2_deploy.sh status    is it done yet?
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh

if [ "${1:-}" = "status" ]; then
  say "agents-cli deploy --status"
  agents-cli deploy --status 2>&1 | grep -v "npx\|Node.js"
  exit
fi
say "agents-cli deploy --agent-identity --no-wait   (project: $PROJECT)"
agents-cli deploy --agent-identity --no-wait --project "$PROJECT" 2>&1 | grep -v "npx\|Node.js"
