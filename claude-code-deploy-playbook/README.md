# Claude Code Deployment Playbook: Hetzner, Coolify and Tailscale (Claude Team Plan)

How a two-person team can use **Claude Code** to write and deploy **Node.js** apps to **Hetzner Cloud** with **Coolify**, behind **Tailscale**, on a **Claude Team** plan. This guide covers safe guardrails, `CLAUDE.md` templates, permission settings, and Dockerfiles.

> **Facts checked on 2026-11-20** against Anthropic, Claude Code, Node.js and Coolify documentation (sources at the end). Prices and limits change, so check the linked pages before you buy.
>
> This page started as a Google AI Mode answer. That answer was reviewed, and the mistakes and risky advice in it were corrected. See [What was corrected](#what-was-corrected-from-the-original-ai-answer).

## Contents

1. [Summary](#summary)
2. [Claude Team plan: cost and limits](#claude-team-plan-cost-and-limits)
3. [The most important rule: CLAUDE.md is guidance, settings are enforcement](#the-most-important-rule-claudemd-is-guidance-settings-are-enforcement)
4. [Recommended workflow: Claude writes, Git deploys](#recommended-workflow-claude-writes-git-deploys)
5. [Setup on each Windows laptop](#setup-on-each-windows-laptop)
6. [Setup in each client repository](#setup-in-each-client-repository)
7. [Server-side safety nets](#server-side-safety-nets)
8. [Token and usage tips](#token-and-usage-tips)
9. [What was corrected from the original AI answer](#what-was-corrected-from-the-original-ai-answer)
10. [FAQ](#faq)
11. [Sources](#sources)

## Summary

- **Plan:** Claude Team with **2 Premium seats**. That is **$250/month billed monthly** or **$200/month billed annually** ($2,400 per year), plus tax.
- **Safety model:** Claude Code writes code and opens pull requests. **Coolify deploys from Git.** Claude never gets direct access to the LIVE server.
- **Enforcement:** put hard rules in `settings.json` permission rules, not only in `CLAUDE.md`.
- **Secrets:** they live in Coolify. They are blocked from Claude's file tools and kept out of Docker images with `.dockerignore`.
- **Runtime:** Node.js **24 LTS** or newer. Node 22 reaches end of life on 2027-04-30.

## Claude Team plan: cost and limits

| Item | Verified detail |
| --- | --- |
| Premium seat | $125 per member/month billed monthly, $100 per member/month billed annually |
| Standard seat | $25 billed monthly, $20 billed annually |
| Seat count | Minimum 2 members, maximum 150 seats |
| 2 Premium seats | $250/month (monthly) or $200/month (annual, $2,400/year) |
| Usage limits | Per member, not shared. A five-hour session limit plus a weekly limit across all models. Premium = 6.25× Pro's per-session allowance, Standard = 1.25× |
| Extra usage | Admins can turn on prepaid usage credits so members keep working after hitting limits. Spending caps can be set for the organization, and for individual users *where available* |

**Recommendation:** start with monthly billing for the first month, then switch to annual once you know Premium is right for you. Turn on usage credits with a modest spending cap (for example about $25 per member per month) so an urgent deployment isn't blocked by a usage limit.

> ⚠️ **Not verified:** the AI answer said the invoice shows your company name, tax ID and billing address. The official Team plan article doesn't say this. Check under **Settings → Billing** in claude.ai before you rely on it for accounting.

## The most important rule: CLAUDE.md is guidance, settings are enforcement

The Claude Code docs say it directly: *"Permission rules are enforced by Claude Code, not by the model. Instructions in your prompt or `CLAUDE.md` shape what Claude tries to do, but they don't change these rules."*

So use three layers:

| Layer | File | What it does |
| --- | --- | --- |
| Guidance | `CLAUDE.md` (global + per repo) | Tells Claude your architecture, conventions and intentions |
| Enforcement | `settings.json` permission rules | **Blocks** reading secrets, **asks** before `ssh`, `git push`, `hcloud`, and so on, and turns off "bypass permissions" mode |
| Hard boundary | Your servers, Git and Tailscale | Claude's machine never holds LIVE credentials, so a mistake can't reach LIVE |

Two limits from the docs that matter for security:

- A `Bash(ssh *)` rule matches the command as Claude usually writes it. It is **not a security boundary**: it won't catch `sh -c 'ssh …'` or a full path to the program. The real protection is that LIVE credentials aren't reachable (layer 3).
- `Read` deny rules protect Claude's file tools and common commands like `cat`. They don't stop a script Claude runs from opening a file itself.

## Recommended workflow: Claude writes, Git deploys

```text
Laptop (Claude Code)              GitHub                     Hetzner
──────────────────────            ──────                     ───────
feature branch ──► pull request ──► CI: tests + lint
                                    │
                    human review ◄──┘
                         │
          merge to test branch ─────► Coolify TEST deploys (mock data)
                         │                 human checks preview
          merge to main ────────────► Coolify LIVE deploys (real data)
```

Why this works:

- **Claude never needs LIVE access.** Deploying is just a merge, and a human approves every merge.
- **Every change can be reviewed and undone.** You roll back by redeploying the previous commit in Coolify.
- **Protect it in GitHub:** add branch protection on `main` (require a pull request and passing checks). That way neither a person nor Claude can push to LIVE directly.
- **Watch out for prompt injection:** Claude reads web pages, issues, logs and emails. Text in any of those can try to steer it. The layers above mean that even a successful injection can't deploy to LIVE.

## Setup on each Windows laptop

The templates are in [`templates/`](templates/). Run these in PowerShell from this folder.

1. **Global `CLAUDE.md`** (guidance). This backs up any existing file first:

   ```powershell
   $dest = "$env:USERPROFILE\.claude"
   New-Item -ItemType Directory -Force -Path $dest | Out-Null
   if (Test-Path "$dest\CLAUDE.md") { Copy-Item "$dest\CLAUDE.md" "$dest\CLAUDE.md.bak" }
   Copy-Item ".\templates\global-CLAUDE.template.md" "$dest\CLAUDE.md"
   ```

2. **Global permission rules** (enforcement). If `%USERPROFILE%\.claude\settings.json` **already exists**, merge the `permissions` block from [`templates/user-settings.json`](templates/user-settings.json) into it by hand. If it doesn't exist, copy it:

   ```powershell
   if (-not (Test-Path "$env:USERPROFILE\.claude\settings.json")) { Copy-Item ".\templates\user-settings.json" "$env:USERPROFILE\.claude\settings.json" }
   ```

   What it does:
   - **Blocks** Claude's file tools from reading `.env`, `.env.*` (except `.env.example`), `*.pem`, `*.key`, and `~/.ssh/`.
   - **Asks you first** before `ssh`, `scp`, `rsync`, `git push`, `hcloud`, or `tailscale` commands, in both Bash and PowerShell, even in auto mode.
   - **Turns off** `bypassPermissions` mode on that laptop.

3. **Separate keys:** use a passphrase-protected SSH key (or Tailscale SSH) for servers, and never put LIVE keys in a project folder.

## Setup in each client repository

| Template | Copy to | Commit? |
| --- | --- | --- |
| [`project-CLAUDE.template.md`](templates/project-CLAUDE.template.md) | `CLAUDE.md` | Yes |
| [`project-settings.json`](templates/project-settings.json) | `.claude/settings.json` | Yes, so both engineers share the rules |
| [`Dockerfile`](templates/Dockerfile) (Express/Fastify/NestJS) or [`Dockerfile.nextjs`](templates/Dockerfile.nextjs) | `Dockerfile` | Yes |
| [`.dockerignore`](templates/.dockerignore) | `.dockerignore` | Yes, **required** |
| — | `.env.example` with placeholder values only | Yes |
| — | `.env` in `.gitignore` | Never commit `.env` |

The per-repo `CLAUDE.md` repeats the critical guardrails on purpose. **Your global `~/.claude/CLAUDE.md` isn't loaded in Claude Code cloud sessions** (claude.ai/code), or on a machine where it was never installed.

**Dockerfile notes:**

- Both use `node:24-alpine`, `npm ci` with a committed lockfile, a non-root user, and `tini` for clean shutdowns during Coolify redeploys.
- **Coolify health checks:** an HTTP check needs `curl` or `wget` *inside* the image. Alpine includes BusyBox `wget`. Point the check at your `/health` route.
- **Nixpacks vs Dockerfile:** Nixpacks is in maintenance mode, and Coolify marks its successor Railpack as beta. A Dockerfile gives you predictable builds.

## Server-side safety nets

- **Tailscale ACLs:** restrict who and which devices can reach LIVE SSH and the LIVE Coolify dashboard. Consider Tailscale SSH *check mode*, which requires a fresh login before each session.
- **Firewall lockout:** before any firewall change, keep a second Tailscale session open, and know where the Hetzner Console (out-of-band access) is.
- **Backups:** an untested backup isn't a backup. Restore a LIVE backup each month to a **temporary, LIVE-grade server** that you destroy afterwards. Don't restore to TEST: that would put real customer data on TEST and break your own data rule.
- **Secret scanning:** run a scanner such as `gitleaks` in CI to catch committed secrets.

## Token and usage tips

- **Pick the model with `/model`.** Writing "use Sonnet" in `CLAUDE.md` doesn't switch models. For routine work, a faster model saves usage. Switch to the most capable model for hard debugging and architecture.
- **Keep `CLAUDE.md` short.** It's loaded at the start of every session, so every line costs tokens every time.
- **Use `/compact`** to shrink history mid-task, and **`/clear`** between unrelated tasks.
- **Ask for focused edits** ("change only X in file Y") rather than whole-file rewrites.

## What was corrected from the original AI answer

| Original claim | Status | Correction |
| --- | --- | --- |
| 2 Premium seats: $250/mo monthly, $200/mo annual | ✅ Correct | Matches Anthropic's pricing (excl. tax) |
| "5-hour cap" | ✅ Mostly | There's a five-hour session limit **and** a weekly limit, per member |
| Extra usage with a $25/seat cap | ⚠️ Partly | Usage credits exist. Per-user caps apply "where available". $25 is a suggestion, not a plan feature |
| Invoice shows company name, tax ID, address | ⚠️ Unverified | Not stated in the official Team plan article. Check billing settings |
| `CLAUDE.md` "enforces security rules automatically" | ❌ Wrong | `CLAUDE.md` is guidance only. Enforce with `settings.json` permission rules |
| "Default to Sonnet, use Opus for complex work" (in `CLAUDE.md`) | ❌ No effect | Claude can't switch its own model from `CLAUDE.md`. Use `/model` |
| `CLAUDE.md` "prevents wasting tokens scanning the repo" | ⚠️ Overstated | It gives context, and a long file *adds* tokens to every session |
| `node:22-alpine` | ⚠️ Outdated | Node 22 is in maintenance (EOL 2027-04-30). Use 24 LTS or newer |
| Dockerfile `COPY . .` with no `.dockerignore` | ❌ Security risk | Can bake `.env` and `.git` into image layers. A `.dockerignore` is now required |
| `package-lock.json*` (optional lockfile) | ⚠️ Weak | Require a committed lockfile for reproducible builds |
| PowerShell `Set-Content` installer | ⚠️ Risky | Overwrote an existing `CLAUDE.md` with no backup. Replaced with backup-then-copy |
| Global `CLAUDE.md` covers everything | ⚠️ Incomplete | Not loaded in cloud sessions. Repeat guardrails in each repo's `CLAUDE.md` |
| Restore/test with real data | — | Added: restore drills go to a throwaway LIVE-grade server, never TEST |

## FAQ

**Is Claude Team billed per seat or by usage?**
Per seat. Each member has their own usage limits. Optional prepaid usage credits let members keep working after they hit a limit, with spending caps you control.

**Is Claude Team usage unlimited?**
No. Each member has a five-hour session limit and a weekly limit. Premium seats get 6.25× the Pro plan's per-session allowance.

**Can Claude Code deploy to production safely?**
Yes, if Claude never holds production credentials. Let Claude write code and open pull requests. A human merges, and Coolify deploys from Git.

**Does `CLAUDE.md` stop Claude from running dangerous commands?**
No. It's guidance. Use `permissions.deny` and `permissions.ask` in `settings.json`, and keep LIVE credentials off the machine Claude runs on.

**Which Node.js version should a new project use in late 2026?**
A supported LTS line: Node 24 (end of life April 2028) or newer. Avoid starting on Node 22 (end of life April 2027).

## Sources

- [Claude plans & pricing](https://claude.com/pricing)
- [What is the Team plan? (Claude Help Center)](https://support.claude.com/en/articles/9266767-what-is-the-team-plan)
- [Claude Code: Configure permissions](https://code.claude.com/docs/en/permissions)
- [Claude Code: How Claude remembers your project (CLAUDE.md)](https://code.claude.com/docs/en/memory)
- [Claude Code: Settings](https://code.claude.com/docs/en/settings)
- [Node.js release schedule](https://github.com/nodejs/release)
- [Coolify: Health checks](https://coolify.io/docs/applications/configuration/health-checks)
- [Coolify: Build packs](https://coolify.io/docs/applications/build-packs)
