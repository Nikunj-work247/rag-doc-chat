# Nginx Deployment Guide for AWS EC2

This directory contains Nginx configurations optimized for deploying the RAG Document Chat app (Streamlit UI + FastAPI Backend) on AWS EC2.

---

## Files

- **`app.conf`**: Use when Nginx is installed directly on the EC2 host (Ubuntu / Amazon Linux 2023) proxying local services (`127.0.0.1:8501` and `127.0.0.1:8000`).
- **`nginx-docker.conf`**: Use if running Nginx as a container inside `docker-compose.yml` proxying container service names (`frontend` and `backend`).

---

## Key Configurations Handled

1. **Streamlit WebSocket**: Configured with `Upgrade` and `Connection` headers and `proxy_read_timeout 86400s` to prevent the chat UI from disconnecting.
2. **Streaming Tokens**: `proxy_buffering off` is enabled on `/` and `/api/` so LLM token streaming appears in real time.
3. **File Upload Limit**: `client_max_body_size 100M` ensures large PDFs/documents can be uploaded without getting `413 Request Entity Too Large` errors.
4. **Backend Routing**:
   - `/` $\rightarrow$ Streamlit frontend UI
   - `/_stcore/stream` $\rightarrow$ Streamlit WebSocket
   - `/api/` $\rightarrow$ FastAPI REST endpoints
   - `/docs` $\rightarrow$ Swagger interactive API docs

---

## Option 1: Direct EC2 Host Setup (Recommended)

### 1. Security Group Configuration
In your AWS EC2 Console, ensure your EC2 Security Group inbound rules allow:
- **Port 80 (HTTP)** from `0.0.0.0/0`
- **Port 443 (HTTPS)** from `0.0.0.0/0`
- **Port 22 (SSH)** from your IP

*(You no longer need to expose ports 8501 or 8000 directly to the public internet).*

### 2. Install Nginx on EC2

#### On Ubuntu / Debian:
```bash
sudo apt update
sudo apt install -y nginx
```

#### On Amazon Linux 2023:
```bash
sudo dnf install -y nginx
```

### 3. Deploy the Configuration

#### On Ubuntu / Debian:
```bash
# Copy configuration
sudo cp nginx/app.conf /etc/nginx/sites-available/rag-doc-chat.conf

# Enable site and remove default
sudo ln -sf /etc/nginx/sites-available/rag-doc-chat.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

#### On Amazon Linux 2023:
```bash
sudo cp nginx/app.conf /etc/nginx/conf.d/rag-doc-chat.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 4. Setup Free SSL / HTTPS (Let's Encrypt Certbot)
If you have a domain pointed to your EC2 Public IP:

```bash
# Ubuntu:
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Amazon Linux 2023:
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```
Certbot will automatically update the Nginx configuration with SSL certificates and HTTP-to-HTTPS redirection.

---

## Option 2: Running Nginx in Docker Compose

If you prefer Nginx running as a Docker container, add this service to `docker-compose.yml`:

```yaml
  nginx:
    image: nginx:alpine
    container_name: rag-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx-docker.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
```
Then start the stack:
```bash
docker compose up -d
```

