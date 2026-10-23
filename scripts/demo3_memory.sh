#!/usr/bin/env bash
# Demo 3, Remember: on the pre-deployed agent (AGENT_ID, default: the backup).
#   ./scripts/demo3_memory.sh           session 2 + stored memories (ayse is already seeded)
#   ./scripts/demo3_memory.sh full      session 1, wait for Memory Bank, session 2
#   ./scripts/demo3_memory.sh seed      session 1 only (seed a fresh agent)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh
case "${1:-}" in
  full) uv run python scripts/demo3_memory.py ;;
  seed) uv run python scripts/demo3_memory.py --seed ;;
  *)    uv run python scripts/demo3_memory.py --recall ;;
esac
