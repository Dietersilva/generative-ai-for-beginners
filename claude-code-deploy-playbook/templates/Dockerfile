# Generic Node.js (TypeScript) app for Coolify: Express, Fastify, NestJS, etc.
# Assumes: package-lock.json is committed, `npm run build` compiles to ./dist,
# and the entry point is dist/index.js. Pair with the .dockerignore in this folder.

FROM node:24-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:24-alpine AS runner
# tini forwards SIGTERM to Node and reaps zombie processes (clean Coolify redeploys)
RUN apk add --no-cache tini
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Files stay owned by root, so the app (running as "node") cannot modify its own code
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist

USER node
EXPOSE 3000
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "dist/index.js"]
