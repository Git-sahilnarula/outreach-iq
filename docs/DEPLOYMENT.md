# Outreach IQ — Production Deployment & Operations Manual

This guide walks you through deploying **Outreach IQ** in production using Docker Compose, PostgreSQL, automated Let's Encrypt SSL certificates, and health monitoring.

---

## 🏛️ Architecture Overview

```
                      Internet (HTTPS Port 443)
                                 │
                                 ▼
                     [Reverse Proxy / Nginx / Caddy]
                     (SSL Termination + Asset Cache)
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
                 ▼ /api/*                        ▼ /*
      [FastAPI Backend Container]      [React SPA Static Container]
      • Port 8000                      • Nginx Alpine
      • Automatic DB Migrations        • Gzip Compression
      • Non-root secure runtime        • SPA History Fallback
                 │
        ┌────────┴────────┐
        ▼                 ▼
[PostgreSQL 16]      [Ollama / LLM]
(Persistent Data)    (AI Scoring & Pitches)
```

---

## 🚀 Quick Start: Docker Compose

### 1. Clone & Prepare Environment

```bash
git clone https://github.com/your-org/outreach-iq.git
cd outreach-iq
cp .env.example .env
```

Edit `.env` and configure your production secrets:
```ini
# Crucial: generate a strong 32+ character key
JWT_SECRET=your_super_strong_random_secret_here_32_characters_minimum

# Your production domain
CORS_ORIGINS=https://outreach.yourdomain.com

# PostgreSQL credentials
POSTGRES_DB=outreach_iq
POSTGRES_USER=outreach_user
POSTGRES_PASSWORD=generate_a_secure_postgres_password_here
```

### 2. Launch Stack

For standard deployments with PostgreSQL:
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Verify all containers are running and healthy:
```bash
docker compose -f docker-compose.prod.yml ps
```

### 3. Preload the Ollama AI Model

If utilizing local Ollama in Docker:
```bash
docker compose -f docker-compose.prod.yml exec ollama ollama pull qwen3:8b
```

---

## 🔒 SSL & Reverse Proxy Setup

### Option A: Automatic SSL with Caddy (Recommended)

Caddy automatically provisions and renews Let's Encrypt SSL certificates:

Create `/etc/caddy/Caddyfile`:
```caddy
outreach.yourdomain.com {
    reverse_proxy localhost:80
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

### Option B: Nginx with Certbot

```nginx
server {
    server_name outreach.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 80;
}
```

Run Certbot to obtain SSL:
```bash
sudo certbot --nginx -d outreach.yourdomain.com
```

---

## 🩺 System Health Monitoring

Outreach IQ exposes active telemetry at `GET /api/health`:

```bash
curl -s https://outreach.yourdomain.com/api/health | jq .
```

### Expected Output:
```json
{
  "status": "healthy",
  "service": "outreach-iq-api",
  "version": "1.0.0",
  "timestamp": "2026-09-23T17:30:00.000000Z",
  "checks": {
    "database": "connected",
    "ai_provider": "connected"
  }
}
```

You can point tools like **Uptime Kuma**, **Datadog**, or **Better Uptime** to `/api/health` for 24/7 uptime monitoring.

---

## 💾 Database Backups & Maintenance

### Automated Daily Backups

Add a daily cron job to backup PostgreSQL:

```bash
sudo crontab -e
```

Add the following line (runs every day at 3:00 AM):
```cron
0 3 * * * docker compose -f /path/to/outreach-iq/docker-compose.prod.yml exec -T postgres pg_dump -U outreach_user outreach_iq | gzip > /backups/outreach_iq_$(date +\%F).sql.gz
```

### Applying Migrations Manually

Migrations run automatically on container startup via `entrypoint.sh`. If you ever need to apply them manually:
```bash
docker compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

---

## ⚡ GPU Acceleration for Ollama (Optional)

To enable NVIDIA GPU acceleration for Ollama in Docker:
1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
2. In `docker-compose.prod.yml`, add the `deploy` block to the `ollama` service:
```yaml
  ollama:
    image: ollama/ollama:latest
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```
