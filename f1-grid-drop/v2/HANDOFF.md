# F1 Bezerk v2.0: starting a new session

Use this file to pick up work on F1 Bezerk v2.0 in a new Claude Code session, on your own computer or in the cloud.

## Where everything is

| What | Where |
|---|---|
| Repository | `dietersilva/generative-ai-for-beginners` |
| Branch | `claude/youthful-cerf-49o4ha` (don't use `claude/optimistic-dirac-orjjnb`) |
| The game | `f1-grid-drop/v2/index.html`: one file, about 3,400 lines |
| Assets | `f1-grid-drop/v2/assets/`: textures, sky, plant atlases, rocks |
| Feature notes for every round | `f1-grid-drop/v2/README.md` |
| Progress page source | `f1-grid-drop/v2/progress/index.html` |
| Download package | `f1-grid-drop/releases/F1-Bezerk-v2.0/` and `F1-Bezerk-v2.0.zip` |
| v1.0 (locked, don't change) | `f1-grid-drop/index.html` and `f1-grid-drop/releases/F1-Bezerk-v1.0/` |
| Live v2.0 page | https://claude.ai/artifact/51RaQNnxXYXN9voVZQa2Vx |
| Live progress page | https://claude.ai/artifact/NoagHvUYA67fxdHe5G9syZ |

## Set up on your computer

1. Get the code:

   ```bash
   git clone https://github.com/dietersilva/generative-ai-for-beginners.git
   ```

   ```bash
   cd generative-ai-for-beginners
   ```

   ```bash
   git checkout claude/youthful-cerf-49o4ha
   ```

2. Run the game. Serve it from a local web server rather than double-clicking it. Opened as a file, the page skips the real textures and sky.

   ```bash
   cd f1-grid-drop/v2 && python3 -m http.server 8000
   ```

   Then open http://localhost:8000 in Chrome.

3. Start Claude Code in the repository folder and paste the prompt below.

## What works locally and what doesn't

- **Works:** the race, physics, cameras, the director camera, commentary, replays, sound, TV graphics, the race setup menu, the championship and pass-and-play betting.
- **Needs the live claude.ai page:** shared phone betting (`#bet`), the phone watch view (`#watch=CODE`), cheering and the spoken voices. They use the page's capabilities (`db`, `room`, `user`, `tts`), which only exist on claude.ai.
- **Updating the live page:** publishing goes through Claude's Artifact tool, with the `url` above. That tool may not be available in every Claude Code setup. If it isn't, commit and push, then publish from a cloud session at claude.ai/code.

## Prompt for the new session

Paste this as the first message:

```text
I'm continuing work on F1 Bezerk v2.0, a fan-made 3D F1 soapbox race game for personal use.

- Read f1-grid-drop/v2/HANDOFF.md and f1-grid-drop/v2/README.md first.
- Work only in f1-grid-drop/v2/. v1.0 (f1-grid-drop/index.html and releases/F1-Bezerk-v1.0) is locked.
- Use branch claude/youthful-cerf-49o4ha. Commit and push after every change.
- The live page is https://claude.ai/artifact/51RaQNnxXYXN9voVZQa2Vx. It needs the capabilities db (rule: pool, read view, write admin), room, user and tts. Keep them when you republish.
- Tech: three.js 0.160.0 and cannon-es 0.20.0 from jsDelivr with pinned versions, plus Poly Haven CC0 assets.
- Watch out for // comments: in the past they swallowed code on the same line. Use /* */ for inline comments.
- After each round, add notes to v2/README.md, update the progress page, and rebuild releases/F1-Bezerk-v2.0.zip with a new SHA-256 in RELEASE-NOTES.md.
- When I give you a list, make a task list and finish and test each task before moving on.
- Be honest about what you tested and what you couldn't check.
```

## Ideas not yet done

- Tyre lettering is only readable up close. It could be made bigger, or shown in onboard shots only.
- The sound has never been checked by ear. Tune it to your taste.
- The phone replay camera was moved back after it started inside the T-rex's mouth. That fix hasn't been re-tested.
- The game isn't photoreal. That would need a game engine such as Unreal, not a browser page.

## Privacy and legal

- The game has no analytics or tracking. Settings are saved only in the browser.
- A private fan project, not affiliated with Formula 1. Sharing it publicly would need licences for the driver names, team colours and trademarks.
