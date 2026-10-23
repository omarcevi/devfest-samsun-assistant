#!/usr/bin/env bash
# Demo 4, Observe: the Cloud Trace waterfall of the last demo3 "session 2" request, plus its console link.
#   ./scripts/demo4_trace.sh [SESSION_ID]
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh
uv run python scripts/trace_link.py "$@"
