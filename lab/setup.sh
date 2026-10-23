#!/usr/bin/env bash
# Prepares Cloud Shell for the DevFest Samsun lab. Safe to run more than once.
# Run it from the repo root:  ./lab/setup.sh
set -uo pipefail

AGENTS_CLI_VERSION="1.11.0"
APIS=(
  aiplatform.googleapis.com          # Gemini, Agent Runtime, Sessions, Memory Bank
  cloudtrace.googleapis.com          # the Trace tab
  telemetry.googleapis.com           # where the agent sends its traces
  logging.googleapis.com             # agent logs
  cloudresourcemanager.googleapis.com # lets the deploy grant the agent its IAM roles
  apphub.googleapis.com              # the agent's Dashboard tab asks for it
)

ok()   { echo "✅ $*"; }
fail() { echo "❌ $*"; exit 1; }

cd "$(dirname "$0")/.." || exit 1
PATH_AT_START="$PATH"

# 1. Project
PROJECT="$(gcloud config get-value project 2>/dev/null)"
[ -n "$PROJECT" ] || fail "No project set. Run \`gcloud config set project YOUR_PROJECT_ID\` first."
gcloud projects describe "$PROJECT" --format="value(projectId)" >/dev/null 2>&1 \
  || fail "Can't open project '$PROJECT'. Check the Project ID (not the name) and run \`gcloud config set project YOUR_PROJECT_ID\` again."
ok "Project: $PROJECT"

# 2. Billing
BILLING="$(gcloud billing projects describe "$PROJECT" --format="value(billingEnabled)" 2>/dev/null)"
[ "$BILLING" = "True" ] || fail "Billing isn't linked to $PROJECT. In the console open Billing › Link a billing account, pick your credits account, then run ./lab/setup.sh again."
ok "Billing is linked"

# 3. APIs (takes about a minute the first time)
gcloud services enable "${APIS[@]}" --project "$PROJECT" --quiet >/dev/null 2>&1 \
  || fail "Couldn't turn on the Google Cloud APIs. Wait a minute and run ./lab/setup.sh again."
ok "APIs turned on: Agent Platform, Trace, Telemetry, Logging, Resource Manager, App Hub"

# 4. uv, the agent's Python packages and the Agents CLI
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || fail "Couldn't install uv. Check your connection and run ./lab/setup.sh again."
fi
ok "uv $(uv --version | cut -d' ' -f2)"

uv sync --quiet 2>/dev/null || fail "Couldn't install the agent's Python packages. Run ./lab/setup.sh again."
ok "Agent packages installed (ADK $(uv run --quiet python -c 'import google.adk; print(google.adk.__version__)'))"

if [ "$(agents-cli --version 2>/dev/null | awk '{print $NF}')" != "$AGENTS_CLI_VERSION" ]; then
  uv tool install --quiet --force "google-agents-cli==$AGENTS_CLI_VERSION" >/dev/null 2>&1 \
    || fail "Couldn't install the Agents CLI. Run ./lab/setup.sh again."
fi
ok "Agents CLI $AGENTS_CLI_VERSION"

# 5. .env: the agent calls Gemini in your project. "global" spreads load across regions.
cat > .env <<ENV
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=$PROJECT
GOOGLE_CLOUD_LOCATION=global
ENV
ok ".env written"

# 6. Next step. A new tool folder only reaches your shell's PATH after you reload it.
case ":$PATH_AT_START:" in
  *":$HOME/.local/bin:"*) echo "✅ Ready. Next: uv run adk web --port 8080 --allow_origins \"*\"" ;;
  *) echo "✅ Ready. Run this once:  source ~/.profile"
     echo "   Next: uv run adk web --port 8080 --allow_origins \"*\"" ;;
esac
