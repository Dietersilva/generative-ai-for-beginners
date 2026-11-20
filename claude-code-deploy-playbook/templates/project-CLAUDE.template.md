# Client Project: [Client Name]

<!--
Commit this file to each client repo as CLAUDE.md (repo root).
It repeats the critical guardrails on purpose: the global file in
%USERPROFILE%\.claude\ is NOT loaded in cloud sessions or on a machine
where it was never installed.
-->

## Project
- Framework: [Express / Fastify / NestJS / Next.js] on Node.js [24] (TypeScript)
- Database / ORM: PostgreSQL + [Prisma / Drizzle]
- TEST URL: `https://[client].test.example.com` (mock data only)
- LIVE URL: `https://[client-domain]` (real data)
- Notes: [e.g. Stripe webhooks, transactional email provider]

## Commands
- Install: `npm ci`
- Dev: `npm run dev`
- Test / lint: `npm test` / `npm run lint`
- Seed mock data (local and TEST only): `npm run db:seed`
- Migrate: `[npx prisma migrate deploy | npx drizzle-kit migrate]`

## Guardrails (non-negotiable)
- Deploy only by Git: feature branch, then pull request, then merge. Coolify deploys. No SSH or Coolify API calls against LIVE.
- Never read, print, or commit secrets. Only `.env.example` holds placeholders.
- No real customer data outside LIVE.
- Keep `.dockerignore` excluding `.env*` (except `.env.example`), `.git`, and key files.
