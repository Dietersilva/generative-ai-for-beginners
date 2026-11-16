# AI-Meter: AI subscription usage and cost per job

AI-Meter is a small Windows app that shows how much of your AI plans you've used
(Claude, ChatGPT, MiniMax Code and any tool you add). It also turns your monthly
subscription bills into a **cost per job**, so you know what each project really
cost you in AI.

Everything runs on your own PC. Nothing is uploaded.

## What it shows

| Tool | Plan usage % | Time per chat / job | Where the data comes from |
|---|---|---|---|
| Claude in the browser (chats + Claude Code on claude.ai) | ✅ 5-hour and weekly | ✅ | Browser extension |
| ChatGPT in the browser (incl. Work/Business) | ❌ OpenAI doesn't publish one for chat | ✅ | Browser extension |
| MiniMax Code desktop app | ✅ 5-hour, weekly and credits | ✅ | MiniMax Code's own files on this PC (read-only) |
| Claude Code / Codex CLI on this PC | Codex: ✅ · Claude Code: shares the Claude plan above | ✅ | Their log files on this PC |
| Your own tools (websites or desktop apps) | ❌ | ✅ | Browser extension / active window (Windows) |

## How cost per job works

At month end you know what each subscription cost and how much time went into
each job. AI-Meter does the split for you, **per subscription**:

```
cost of a job = monthly price x (time on that job with that tool / all time with that tool)
```

* **Time means active time.** Browser: the tab is in front and you've used the
  mouse or keyboard in the last few minutes. Coding agents: time between their
  steps, with breaks longer than the idle cutoff (default 5 minutes) removed.
* **Each subscription is split on its own.** An hour on a $200 plan costs more
  than an hour on a $20 plan.
* A subscription you didn't use shows up as **"Unused subscription"**, so the
  total always matches what you paid. That's a signal to downgrade.
* **Jobs** come from, in order: what you type on a chat, then your **rules**
  ("title contains *router* → *Home network*"), then the project folder name.
  Everything else is **Unassigned**.
* **Optional split by tokens** for tools that log tokens (Claude Code, Codex,
  MiniMax). Browser chats don't expose tokens, so they always use time.
* **Export CSV** for invoicing. Chat titles are made safe so they can't run as
  spreadsheet formulas.

The numbers are an estimate. Providers don't publish a cost per chat for flat-rate
plans, so time is the fairest measure available.

## Install (Windows)

1. Get the build: from GitHub **Actions → AI-Meter Windows build → artifact**,
   or build it yourself with `build.ps1` (needs Python 3.11+).
2. Run the installer:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -StartWithWindows
   ```

   This installs to `%LOCALAPPDATA%\Programs\AI-Meter` with no admin rights,
   creates shortcuts, sets **Ctrl+Alt+M** to show or hide the overlay, and opens
   the dashboard.
3. Windows SmartScreen may warn because the exe isn't code-signed. Choose
   **More info → Run anyway** only if you built it yourself or got it from your
   own GitHub Actions run.
4. In the dashboard, go to **Settings → Subscriptions** and enter what you pay
   per month.

### Browser extension (Chrome or Edge)

1. Open `chrome://extensions` (or `edge://extensions`) and turn on **Developer mode**.
2. Click **Load unpacked** and pick `%LOCALAPPDATA%\Programs\AI-Meter\extension`.
3. Its options page opens. Paste the **port** and **pairing token** from the
   dashboard (**Settings → Browser extension pairing**), then click **Save & test**.
4. Keep a claude.ai tab open now and then: that's when the Claude plan % refreshes.

### Run from source (any OS, for testing)

```bash
python -m aimeter              # overlay + dashboard
python -m aimeter --no-overlay # dashboard only, at http://127.0.0.1:47821/
python -m unittest discover -s tests
```

## Adding a new tool

**Settings → Custom tools → Add tool**:

* **Website** (for example `perplexity.ai`): then click **Allow** for it in the
  extension's options page.
* **Desktop app** (for example `cursor.exe`, `Claude.exe`, `ChatGPT.exe`): timed
  while it's the window in front and you're active (Windows).

Then tick the new tool under the subscription that pays for it.

## Privacy and security

* The app listens on **127.0.0.1 only** and needs a random **pairing token** for
  every data request. It also rejects foreign `Host` headers (blocks DNS
  rebinding) and never answers cross-site preflight requests. The dashboard uses
  a strict Content-Security-Policy.
* The extension sends only chat IDs, titles, active seconds and plan percentages
  to `127.0.0.1`. It never reads message contents and never sends cookies or logins.
* The Claude plan % comes from the same internal endpoint that claude.ai's own
  **Settings → Usage** page uses. Anthropic doesn't document it, so it may change
  without notice. If it does, only that one number stops updating.
* MiniMax: the app reads MiniMax Code's login file but **never rewrites it**. If
  the login expires, open MiniMax Code once.
* Settings live in `%APPDATA%\AI-Meter`. The database lives in `%LOCALAPPDATA%\AI-Meter`.
  The pairing token is in `config.json`: don't share that file.
