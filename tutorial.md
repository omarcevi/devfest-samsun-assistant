<walkthrough-metadata>
  <meta name="title" content="Deploy your first AI agent to Google Cloud" />
  <meta name="description" content="DevFest Samsun 2026 lab: run an ADK agent in Cloud Shell, deploy it to Agent Runtime with Agent Identity, and explore it in Agent Platform." />
  <meta name="keywords" content="ADK, Agent Runtime, Agent Identity, Memory Bank, agents-cli, DevFest Samsun" />
</walkthrough-metadata>

# Deploy your first AI agent to Google Cloud

## Welcome

In this lab, you run the **DevFest Samsun Assistant** in Cloud Shell, deploy it to **Agent
Runtime** and explore it in **Agent Platform**. You don't write any code.

The assistant answers questions about the real DevFest Samsun 2026 schedule: which talks are
on, who gives them, when, and on which floor. It's built with the **Agent Development Kit
(ADK)**: one Gemini model, one instruction, and a few Python functions it can call as tools.

![Architecture](https://omarcevi.dev/workshops/devfest-samsun-agent/diagrams/architecture.svg)

| Step | What you do | Time |
|---|---|---|
| 1 | Select your project and run the setup script | 3 min |
| 2 | Talk to your agent locally with `adk web` | 5 min |
| 3 | Deploy it to Agent Runtime | about 5 min |
| 4 | Meet your agent in Agent Platform | 5 min |
| 5 | Clean up | 1 min |

The guide has the same steps on one page, with troubleshooting:
[omarcevi.dev/workshops/devfest-samsun-agent](https://omarcevi.dev/workshops/devfest-samsun-agent/).

<walkthrough-tutorial-duration duration="20"></walkthrough-tutorial-duration>

## Step 1 · Select your project and set up

Select the project you created with your credits. It must have billing linked.

<walkthrough-project-setup billing="true"></walkthrough-project-setup>

1. Point Cloud Shell at this project:
   ```bash
   gcloud config set project <walkthrough-project-id/>
   ```
   If Cloud Shell asks you to authorize gcloud, click **Authorize**.
2. Run the setup script (1–2 minutes):
   ```bash
   ./lab/setup.sh
   ```
   It checks that billing is linked, turns on the APIs this lab needs, installs the agent's
   Python packages and the Agents CLI, and writes a `.env` file so the agent uses Gemini in
   your project.
3. Make your shell use the Agents CLI that the script just installed (Cloud Shell has an
   older one built in):
   ```bash
   source ~/.profile
   ```

✅ **Check:** the script ends with `✅ Ready`, and `agents-cli --version` shows `1.11.0`.

## Step 2 · Talk to your agent locally

First, have a look at the whole agent:
<walkthrough-editor-open-file filePath="app/agent.py">app/agent.py</walkthrough-editor-open-file>.
Its tools are plain Python functions in
<walkthrough-editor-open-file filePath="app/tools.py">app/tools.py</walkthrough-editor-open-file>.

![The agent loop](https://omarcevi.dev/workshops/devfest-samsun-agent/diagrams/step-3-local.svg)

1. Start the ADK dev UI:
   ```bash
   uv run adk web --port 8080 --allow_origins "*"
   ```
   `--allow_origins "*"` lets the Web Preview page talk to the dev UI. Without it the page
   stays blank.
2. Click <walkthrough-web-preview-icon></walkthrough-web-preview-icon> **Web preview**, then
   **Preview on port 8080**. A new tab opens. Check that the agent **`app`** is selected at the
   top left.
3. Ask it something. The first answer can take 20–40 seconds.
   - `Which talks are about AI agents?`
   - `What's on Kat 2 tomorrow?`
   - `Yarın Flutter ile ilgili hangi konuşmalar var?`
4. Above each answer you see small chips: ⚡ `search_sessions` is a tool call, ✓
   `search_sessions` is its result. Click one to see the arguments and the result in the
   left panel. That's the agent loop: the model picks a tool, reads the result, then answers.
5. Go back to the terminal and press **Ctrl+C** to stop the dev UI.

## Step 3 · Deploy it to Agent Runtime

![What agents-cli deploy does](https://omarcevi.dev/workshops/devfest-samsun-agent/diagrams/step-4-deploy.svg)

Run:

```bash
agents-cli deploy --agent-identity -i
```

- It asks `Deploying to Google Cloud project '<walkthrough-project-id/>'. Proceed? [Y/n]`.
  Check that it's yours and press **Enter**. You can ignore the warning about `npx`.
- It packages your code, builds a container and creates a managed agent that scales on its
  own, down to zero when nobody uses it.
- `--agent-identity` gives your agent **its own identity** in IAM, instead of a shared
  service account.
- It takes **about 5 minutes**. Watch the demo on stage while you wait.

✅ **Check:** the output shows `✅ Deployment successful!`, followed by your agent's ID and its
Agent Identity.

The deploy keeps running on Google Cloud even if Cloud Shell disconnects. Reconnect, go back
to this folder, and check progress with:

```bash
agents-cli deploy --status
```

## Step 4 · Meet your agent in Agent Platform

1. Open [Agent Platform › Agents › Deployments](https://console.cloud.google.com/agent-platform/runtimes?project=<walkthrough-project-id/>)
   and click **devfest-samsun-assistant**. If a pop-up says an API isn't enabled, click
   **Close**.
2. **Playground** tab: chat with your *deployed* agent.
   - Ask `Hi! I'm into ML and Flutter. What should I see tomorrow?`
   - Wait about 30 seconds, click **New Session**, and ask `What should I see tomorrow?`.
     It remembers what you like: that's **Memory Bank**.
   - The first answer can take up to a minute while your agent wakes up.
3. **Sessions** tab: every conversation you just had, stored by Agent Runtime.
4. **Memories** tab: the facts Memory Bank kept about you.
5. [Trace explorer](https://console.cloud.google.com/traces/explorer?project=<walkthrough-project-id/>):
   each row is one step of your agent: `invoke_agent`, `generate_content` (a Gemini call) and
   `execute_tool` (a tool call). Click one to see the timeline. Traces show up a minute or two
   after you chat.

![Memory and traces](https://omarcevi.dev/workshops/devfest-samsun-agent/diagrams/step-5-console.svg)

You've now seen, on your own agent, the questions from the talk:
**where it runs** (Agent Runtime), **what it remembers** (Sessions and Memory Bank), **who it
acts as** (its Agent Identity) and **what it's doing** (traces).

## Step 5 · Clean up

Your credits are limited. When you're done, delete the agent:

```bash
./lab/cleanup.sh
```

You can keep it until the end of DevFest on Sunday if you want to play with it more. To
remove everything, shut the project down in
[IAM & Admin › Settings](https://console.cloud.google.com/iam-admin/settings?project=<walkthrough-project-id/>).

## Done

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You ran an ADK agent in Cloud Shell, deployed it to Agent Runtime with its own identity, and
saw its sessions, memories and traces in Agent Platform.

No laptop at hand later? Chat with the shared assistant on your phone:
[omarcevi.dev/demos/devfest-samsun-agent](https://omarcevi.dev/demos/devfest-samsun-agent/).
The code is on [GitHub](https://github.com/omarcevi/devfest-samsun-assistant).
