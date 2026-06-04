# Deploy My Agent in <8 minutes

Pick the path that matches your stack. Each flow ends with a working
`/api/health` and the React app served at `/app`.

## Self-host: Docker compose (recommended for VPS)

```bash
git clone https://github.com/Shugar86/my-agent.git
cd my-agent
cp deploy/.env.example .env
# fill OPENROUTER_API_KEY, JWT_SECRET, ENCRYPTION_KEY, POSTGRES_PASSWORD, DOMAIN
docker compose -f deploy/docker-compose.prod.yml up -d --build
```

Caddy provisions Let's Encrypt automatically once `DOMAIN` resolves to your
server. Visit `https://${DOMAIN}/app` and complete onboarding.

## Render.com (free tier supports the demo path)

1. Fork the repo on GitHub.
2. Open <https://render.com/deploy> and paste your fork URL.
3. Render reads `deploy/render.yaml` and provisions web + Postgres + Redis.
4. Set `OPENROUTER_API_KEY` (and Google OAuth keys, if needed) as secrets.
5. First deploy takes ~5 minutes, then visit `https://<service>.onrender.com/app`.

## Railway

```bash
railway init
railway up --service my-agent
railway variables set OPENROUTER_API_KEY=sk-or-v1-...
railway open
```

`deploy/railway.json` configures the start command and healthcheck.

## Fly.io

```bash
cd deploy
flyctl launch --copy-config --no-deploy
flyctl secrets set OPENROUTER_API_KEY=sk-or-v1-... JWT_SECRET=$(openssl rand -hex 32) ENCRYPTION_KEY=$(openssl rand -hex 32)
flyctl deploy
```

## Health check

Every deployment exposes `GET /api/health` returning a JSON status. Use it
for uptime monitoring and load-balancer health checks. The compose file ships
a Docker healthcheck that uses the same endpoint.

## Rollback

| Platform | Command |
|----------|---------|
| Docker compose | `git checkout v3.0 && docker compose -f deploy/docker-compose.prod.yml up -d --build` |
| Render | "Manual deploy" → previous commit |
| Railway | `railway rollback` |
| Fly.io | `flyctl releases list` then `flyctl deploy --image registry.fly.io/<app>:<release>` |
