#!/usr/bin/env bash
# Demo 1 (fallback for the lab's Step 3): the agent running on this laptop.
#   ./scripts/demo1_local.sh            one question in the terminal
#   ./scripts/demo1_local.sh web        the ADK dev UI on http://localhost:8080
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh

if [ "${1:-}" = "web" ]; then
  say "adk web: open http://localhost:8080 and pick 'app'"
  exec uv run adk web --port 8080
fi
say "The agent, running locally"
uv run python scripts/ask_local.py "Which talks are about AI agents?" 2>/dev/null
