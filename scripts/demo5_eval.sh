#!/usr/bin/env bash
# Demo 5, Evaluate: the time_awareness case fails on v1-bug and passes on v2-fixed.
#   ./scripts/demo5_eval.sh v1-bug     the time_awareness case on v1-bug (about 35 s): fails
#   ./scripts/demo5_eval.sh v2-fixed   the same case on v2-fixed (about 35 s): passes
#   ./scripts/demo5_eval.sh            both, one after the other (about 75 s)
#   ./scripts/demo5_eval.sh full       every eval case on the current code (about 45 s)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source scripts/config.sh
export DEMO_NOW="$DEMO_NOW_FOR_EVALS"   # pin the agent's clock: Saturday 14:00

run_eval() {  # $1 = dataset, $2 = output folder
  mkdir -p "$2"
  agents-cli eval run --dataset "$1" --config evals/eval_config.yaml --output "$2" >"$2/run.log" 2>&1
  uv run python evals/summary.py "$2"
}

if [ "${1:-}" = "full" ]; then
  say "agents-cli eval run: all cases   (clock: Saturday 14:00)"
  run_eval evals/dataset.json artifacts/eval_full
  exit
fi

if ! git diff --quiet HEAD -- app; then
  echo "❌ app/ has uncommitted changes. Commit or stash them first."; exit 1
fi
trap 'git checkout -q HEAD -- app' EXIT   # always put the current code back
TAGS="${1:-v1-bug v2-fixed}"
for tag in $TAGS; do
  git checkout -q "$tag" -- app
  say "$tag   agents-cli eval run: time_awareness   (clock: Saturday 14:00)"
  run_eval evals/time_awareness.json "artifacts/eval_$tag"
done
