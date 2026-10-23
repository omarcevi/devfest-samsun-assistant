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
2. Follow the page to accept the credits. This creates a billing account that uses them.
3. Open the Google Cloud console: <https://console.cloud.google.com>
4. Create a project:
   1. Click the project picker at the top of the page, then **New project**.
   2. **Project name:** `devfest-samsun-agent`
   3. **Billing account:** pick the one with your credits.
   4. Click **Create**.
5. Note your **Project ID**. It's shown under the name and may have numbers added, for example `devfest-samsun-agent-482913`.

✅ **Check:** the top bar of the console shows your new project.

## Step 2: Open Cloud Shell and get the code

**Fastest:** click **[Open in Google Cloud Shell](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/omarcevi/devfest-samsun-assistant.git&cloudshell_git_branch=main&cloudshell_tutorial=tutorial.md&cloudshell_workspace=.&show=ide%2Cterminal)**. In the dialog, tick **Trust repo** and click **Confirm**. (Without *Trust repo*, Cloud Shell runs in ephemeral mode and deletes your files when the session ends.) If asked, click **Authorize**. Cloud Shell clones the code and opens a step-by-step tutorial next to the terminal: follow it from there.

**Or do it by hand:**

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
   source ~/.profile
   ```

   The script:
   - checks that billing is linked to your project
   - turns on the Google Cloud APIs this lab needs
   - installs the agent's Python packages and the Agents CLI
   - writes a `.env` file so the agent uses Gemini in your project

   It takes 1–2 minutes. The last line, `source ~/.profile`, makes your shell use the Agents CLI version the script just installed (Cloud Shell ships an older one).

✅ **Check:** the script ends with `✅ Ready`. If it stops with an error, the message says what to fix. See also **Troubleshooting** at the end.

## Step 3: Talk to your agent locally

1. Start the ADK dev UI:

   ```bash
   uv run adk web --port 8080 --allow_origins "*"
   ```

   `--allow_origins "*"` lets the Cloud Shell Web Preview page talk to the dev UI. Without it the page stays blank.

2. At the top of Cloud Shell, click **Web preview** (the eye icon), then **Preview on port 8080**. A new tab opens.
3. In the top-left dropdown, check that the agent **`app`** is selected.
4. Ask it something:
   - `Which talks are about AI agents?`
   - `What's on Kat 2 tomorrow?`
   - `Yarın Flutter ile ilgili hangi konuşmalar var?`
   The first answer can take 20–40 seconds.
5. Above each answer you'll see small chips: ⚡ `search_sessions` is a tool call, ✓ `search_sessions` is its result. Click one to see the arguments and the result in the left panel. That's the agent loop: the model picks a tool, reads the result, then answers.
6. Go back to Cloud Shell and press **Ctrl+C** to stop the dev UI.

💡 **Optional:** see the whole agent with `cloudshell edit app/agent.py`. It's under 30 lines.

## Step 4: Deploy it to Agent Runtime

Run:

```bash
agents-cli deploy --agent-identity -i
```

- It asks `Deploying to Google Cloud project 'YOUR_PROJECT_ID'. Proceed? [Y/n]`. Check that it's yours and press **Enter**. (`-i` turns this prompt on; without it, the command stops and asks you to name the project.)
- You can ignore the warning about `npx`.
- It packages your code, uploads it and creates a managed agent that scales on its own.
- `--agent-identity` gives your agent **its own identity** in IAM, instead of a shared service account.
- It takes **about 5 minutes**. Leave it running and watch the demo on stage while you wait.

✅ **Check:** the output shows `✅ Deployment successful!`, followed by your agent's ID and its Agent Identity.

The deploy keeps running on Google Cloud even if Cloud Shell disconnects. Click **Reconnect**, run `cd devfest-samsun-assistant`, then check progress with:

```bash
agents-cli deploy --status
```

## Step 5: Meet your agent in Agent Platform

1. In the console's search bar, type **Agent Platform** and open it. In the left menu, click **Agents**, then **Deployments** (under *Scale*).
2. Click your agent: **devfest-samsun-assistant**. If a pop-up says an API isn't enabled, click **Close**.
3. **Playground:** chat with your *deployed* agent. Try:
   - `Hi! I'm into ML and Flutter. What should I see tomorrow?`
   - Wait about 30 seconds, click **New Session** and ask `What should I see tomorrow?`. Does it remember what you like? That's **Memory Bank**.
   - The first answer can take up to a minute while your agent wakes up.
   - In the Playground, click a ⚡ chip to see the tool call, and **State** on the left to see what the agent kept in its session.
4. **Sessions** tab: every conversation you just had, stored by Agent Runtime.
5. **Memories** tab: the facts Memory Bank kept about you, such as your interest in ML and Flutter.
6. **Traces:** in the console's search bar, type **Trace explorer** and open it. Each row is one step of your agent: `invoke_agent`, `generate_content` (a Gemini call) and `execute_tool` (a tool call). Click one to see the timeline, the same view Omar showed on stage. Traces show up a minute or two after you chat.

You've now seen the questions from the talk answered on your own agent:
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
| Web preview shows a blank page | Stop `adk web` with Ctrl+C and start it again with `--allow_origins "*"`, as in Step 3. |
| Cloud Shell says the session ended | Click **Reconnect**, then run `cd devfest-samsun-assistant`. |
| `agents-cli: confirmation required` | Add `-i` to the deploy command, as shown in Step 4. |
| `agents-cli --version` doesn't say `1.11.0` | Run `source ~/.profile`. Cloud Shell has an older Agents CLI built in; this switches to the one `setup.sh` installed. |
| A warning that `npx` isn't installed | Ignore it. |
| A pop-up says `apphub.googleapis.com` isn't enabled | Click **Close**. It doesn't affect the lab. |
| The deploy fails | Copy the last lines of the error and raise your hand. |

## Learn more

- Agent Development Kit (ADK): <https://google.github.io/adk-docs>
- Agent Runtime and Agent Platform: <https://docs.cloud.google.com/gemini-enterprise-agent-platform>
- Agents CLI: <https://pypi.org/project/google-agents-cli/>
- This lab's code: <https://github.com/omarcevi/devfest-samsun-assistant>
