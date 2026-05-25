# Deployment Guide

> My Agent — Production Deployment
> Version: 1.0.0

---

## Quick Start (Local)

### Prerequisites
- Python 3.11+
- pip
- 2GB RAM minimum
- OpenRouter API key

### Step 1: Clone & Setup

```bash
git clone <your-repo-url> my-agent
cd my-agent

# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure

```bash
# Edit config
nano config/agent.json
```

```json
{
  "model": {
    "primary": "openrouter/deepseek/deepseek-v4-flash:free",
    "api_key": "sk-or-v1-YOUR_KEY_HERE",
    "fallback": "openrouter/deepseek/deepseek-chat",
    "params": {
      "temperature": 0.5,
      "max_tokens": 4096
    }
  }
}
```

Or use environment variable:
```bash
export OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"
```

### Step 3: Test

```bash
# Run tests
python -m pytest tests/ -v

# Expected: 20 passed
```

### Step 4: Start Server

```bash
# Development
python -m uvicorn web.server:app --host 127.0.0.1 --port 8000 --reload

# Production (single worker)
python -m uvicorn web.server:app --host 0.0.0.0 --port 8000

# Production (multiple workers)
python -m gunicorn web.server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Step 5: Access

Open browser: `http://localhost:8000`

---

## Docker Deployment

### Build Image

```bash
docker build -t my-agent:latest .
```

### Run Container

```bash
# Basic
docker run -d \
  --name my-agent \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  my-agent:latest

# With volume for persistence
docker run -d \
  --name my-agent \
  -p 8000:8000 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config:/app/config \
  -e OPENROUTER_API_KEY="sk-or-v1-..." \
  my-agent:latest
```

### Docker Compose

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Production Checklist

### Security
- [ ] Change default API key
- [ ] Enable HTTPS (Let's Encrypt / Cloudflare)
- [ ] Set up firewall (ufw/iptables)
- [ ] Add authentication (OAuth2/JWT)
- [ ] Rate limiting (nginx or middleware)
- [ ] Input validation
- [ ] CORS configuration
- [ ] Secret management (Vault/AWS Secrets)

### Performance
- [ ] Use Redis for memory (not JSON files)
- [ ] Add caching layer (Redis/Memcached)
- [ ] Connection pooling for LLM API
- [ ] Async runtime (fix blocking I/O)
- [ ] CDN for static assets
- [ ] Database (PostgreSQL) for agent registry

### Monitoring
- [ ] Application logs (structured JSON)
- [ ] Error tracking (Sentry)
- [ ] Metrics (Prometheus + Grafana)
- [ ] Health checks
- [ ] Alerting (PagerDuty/Opsgenie)

### Backup
- [ ] Agent registry backup
- [ ] Session data backup
- [ ] Config backup
- [ ] Automated backups (daily)

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key |
| `PYTHONIOENCODING` | No | utf-8 | Console encoding |
| `LOG_LEVEL` | No | INFO | Logging level |
| `REDIS_URL` | No | - | Redis connection |
| `DB_URL` | No | - | Database connection |
| `PORT` | No | 8000 | Server port |
| `HOST` | No | 0.0.0.0 | Server host |
| `WORKERS` | No | 1 | Uvicorn workers |
| `MAX_TOKENS` | No | 4096 | LLM max tokens |
| `TEMPERATURE` | No | 0.5 | LLM temperature |

---

## Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

---

## Systemd Service

Create `/etc/systemd/system/my-agent.service`:

```ini
[Unit]
Description=My Agent AI Service
After=network.target

[Service]
Type=simple
User=myagent
WorkingDirectory=/opt/my-agent
Environment=OPENROUTER_API_KEY=sk-or-v1-...
Environment=PYTHONIOENCODING=utf-8
ExecStart=/opt/my-agent/venv/bin/uvicorn web.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable my-agent
sudo systemctl start my-agent
sudo systemctl status my-agent
```

---

## SSL/HTTPS

### Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Cloudflare

1. Add site to Cloudflare
2. Enable proxy (orange cloud)
3. SSL/TLS → Full (strict)
4. Enable "Always Use HTTPS"

---

## Scaling

### Horizontal (Multiple Instances)

```
Users → Load Balancer (Nginx/HAProxy)
           ├── Instance 1 (Port 8000)
           ├── Instance 2 (Port 8001)
           └── Instance 3 (Port 8002)
```

Requirements:
- Shared Redis for memory
- Shared PostgreSQL for registry
- Sticky sessions (optional)

### Vertical (More Resources)

```bash
# Increase workers
python -m gunicorn web.server:app -w 8 --threads 2

# Increase memory
# Upgrade server to 4GB+ RAM
```

---

## Troubleshooting

See TROUBLESHOOTING.md for common issues.

---

## Health Check

```bash
# Check if server is running
curl http://localhost:8000/api/agents

# Expected: JSON with agent list
```

---

End of Deployment Guide
