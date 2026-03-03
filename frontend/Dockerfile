# ---- Builder: install deps and build Next.js standalone ----
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Server-side rewrite destination (Docker service name, not exposed to browser)
ARG REWRITE_API_ORIGIN=http://backend:8000
ENV REWRITE_API_ORIGIN=$REWRITE_API_ORIGIN

RUN npm run build

# ---- Runtime ----
FROM node:22-alpine

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

WORKDIR /app

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
