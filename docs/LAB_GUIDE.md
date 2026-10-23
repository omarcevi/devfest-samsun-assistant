# Deploy your first AI agent to Google Cloud

**DevFest Samsun 2026 · Hands-on lab · about 20 minutes**
Part of *The Google Cloud Stack for Production AI Agents* by Omar Elcircevi

You'll take a ready-made agent, the **DevFest Samsun Assistant**, and run it in Cloud Shell. Then you'll deploy it to **Agent Runtime** on Google Cloud and explore it in **Agent Platform**. You don't write any code, and you don't install anything on your laptop.

## What you need

- A laptop with a browser. Chrome works best.
- A **personal** Google account (Gmail). Work and school accounts often block Cloud Shell or credits.
- The credit link in Step 1.

## The agent

The DevFest Samsun Assistant answers questions about this event's real schedule: which talks are on, when, and on which floor. It's built with Google's **Agent Development Kit (ADK)**. It has one Gemini model, one instruction and a few Python functions it can call as tools.

## The steps

| Step | What you do | Time |
|---|---|---|
| 1 | Get your credits and a project | 5 min |
| 2 | Open Cloud Shell and get the code | 3 min |
| 3 | Talk to your agent locally | 5 min |
| 4 | Deploy it to Agent Runtime | 2 min to start, 5–10 min to finish |
| 5 | Meet your agent in Agent Platform | 5 min |
| 6 | Clean up | 1 min |

---

## Step 1: Get your credits and a project

1. Open the credit link while signed in with your personal Google account: **[CREDIT_LINK]**
2. Follow the page to accept the credits. This creates a billing account that uses them. <!-- VERIFY with Omar: does it ask for a card? What is the billing account called? -->
3. Open the Google Cloud console: <https://console.cloud.google.com>
4. Create a project:
   1. Click the project picker at the top of the page, then **New project**.
   2. **Project name:** `devfest-samsun-agent`
   3. **Billing account:** pick the one with your credits.
   4. Click **Create**.
5. Note your **Project ID**. It's shown under the name and may have numbers added, for example `devfest-samsun-agent-482913`.

✅ **Check:** the top bar of the console shows your new project.

## Step 2: Open Cloud Shell and get the code

1. Click **Activate Cloud Shell** (the `>_` icon) at the top right of the console. If asked, click **Continue** and then **Authorize**.
2. Point Cloud Shell at your project. Replace `YOUR_PROJECT_ID` with your Project ID:

   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. Get the code and run the setup script:

   ```bash
   git clone https://github.com/omarcevi/devfest-samsun-assistant.git
   cd devfest-samsun-assistant
   ./lab/setup.sh
   ```

   The script:
   - checks that billing is linked to your project
   - turns on the Google Cloud APIs this lab needs
   - installs the agent's Python packages and the Agents CLI
   - writes a `.env` file so the agent uses Gemini in your project

   It takes about 2 minutes. <!-- VERIFY: real time on a fresh project -->

✅ **Check:** the script ends with `✅ Ready`. If it stops with an error, the message says what to fix. See also **Troubleshooting** at the end.

## Step 3: Talk to your agent locally

1. Start the ADK dev UI:

   ```bash
   uv run adk web --port 8080
   ```

2. At the top of Cloud Shell, click **Web preview** (the eye icon), then **Preview on port 8080**. A new tab opens.
3. In the top-left dropdown, pick the agent **`app`**. <!-- VERIFY: the name shown in the dropdown -->
4. Ask it something:
   - `Which talks are about AI agents?`
   - `What's on Kat 2 tomorrow?`
   - `Yarın Flutter ile ilgili hangi konuşmalar var?`
5. Click a reply's events to see **which tool the agent called** and what it got back. That's the agent loop: the model picks a tool, reads the result, then answers. <!-- VERIFY: where events show in the current adk web UI -->
6. Go back to Cloud Shell and press **Ctrl+C** to stop the dev UI.

💡 **Optional:** see the whole agent with `cloudshell edit app/agent.py`. It's about 15 lines.

## Step 4: Deploy it to Agent Runtime

Run:

```bash
agents-cli deploy --agent-identity
```

- If it asks you to confirm the project, check that it's yours and press **Enter**. <!-- VERIFY: prompts shown on a fresh project -->
- It packages your code, uploads it and creates a managed agent that scales on its own.
- `--agent-identity` gives your agent **its own identity** in IAM, instead of a shared service account.
- It takes **5–10 minutes**. Leave it running and watch the demo on stage while you wait.

✅ **Check:** the output ends with <!-- VERIFY: exact success line -->.

If Cloud Shell disconnects, click **Reconnect**, run `cd devfest-samsun-assistant`, then check progress with:

```bash
agents-cli deploy --status
```

## Step 5: Meet your agent in Agent Platform

1. In the console's search bar, type **Agent Platform** and open it. Then open **Deployments**. <!-- VERIFY: menu path -->
2. Click your agent. <!-- VERIFY: the name it gets -->
3. **Playground:** chat with your *deployed* agent. Try:
   - `Hi! I'm into ML and Flutter. What should I see tomorrow?`
   - Then click **New session** and ask `What should I see tomorrow?` again. Does it remember what you like? That's **Memory Bank**. Saving a memory can take up to a minute. <!-- VERIFY: memory works across Playground sessions; drop this bullet if not -->
4. **Sessions:** every conversation you just had, stored by Agent Runtime.
5. **Trace:** open one conversation. You'll see the timeline of model calls and tool calls, the same view Omar showed on stage.
6. **Event** and **State:** a graph of what was called, and what the agent kept in its session.

You've now seen the same five questions from the talk on your own agent:
- **where it runs:** Agent Runtime
- **what it remembers:** Sessions and Memory Bank
- **who it acts as:** its Agent Identity
- **what it's doing:** Trace

## Step 6: Clean up

Your credits are limited. When you're done, delete the agent:

```bash
./lab/cleanup.sh
```

You can also shut down the whole project: in the console, go to **IAM & Admin › Settings › Shut down**.

You can keep the agent until the end of DevFest on Sunday if you want to play with it more.

---

## No laptop?

Use the shared assistant on your phone: **[omarcevi.dev/demos/devfest-samsun-agent](https://omarcevi.dev/demos/devfest-samsun-agent)**

## Troubleshooting

| What you see | What to do |
|---|---|
| The setup script says billing isn't linked | In the console, go to **Billing › Link a billing account**, pick your credits account, then run `./lab/setup.sh` again. |
| `PERMISSION_DENIED` or "API not enabled" right after setup | New APIs can take a minute to turn on. Wait, then try again. |
| `429` or `RESOURCE_EXHAUSTED` | You hit a Gemini rate limit. Wait 30 seconds and try again. |
| Web preview shows an error page | Check that `adk web` is still running in Cloud Shell and that you used port 8080. |
| Cloud Shell says the session ended | Click **Reconnect**, then run `cd devfest-samsun-assistant`. |
| The deploy fails | Copy the last lines of the error and raise your hand. |

<!-- VERIFY: add any other error you hit while testing on a fresh project -->

## Learn more

- Agent Development Kit (ADK): <https://google.github.io/adk-docs>
- Agent Runtime and Agent Platform: <https://docs.cloud.google.com/gemini-enterprise-agent-platform>
- Agents CLI: <https://pypi.org/project/google-agents-cli/>
- This lab's code: <https://github.com/omarcevi/devfest-samsun-assistant>
