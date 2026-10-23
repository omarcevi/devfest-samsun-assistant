#!/usr/bin/env bash
# Run this on the morning of the talk. It prints ✅/❌ per thing the demos need.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh
uv run python scripts/check.py
