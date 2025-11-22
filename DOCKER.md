# Docker Deployment Guide for Mooltiproxy

This guide covers deploying Mooltiproxy using Docker and Docker Compose.

> **Windows Users:** See **[DOCKER_WINDOWS.md](DOCKER_WINDOWS.md)** for a complete Windows 11 installation guide including Docker Desktop setup, WSL2 configuration, and step-by-step deployment instructions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Building the Image](#building-the-image)
5. [Running with Docker](#running-with-docker)
6. [Running with Docker Compose](#running-with-docker-compose)
7. [Environment Variables](#environment-variables)
8. [Volume Mounts](#volume-mounts)
9. [Health Checks](#health-checks)
10. [Troubleshooting](#troubleshooting)
11. [Production Deployment](#production-deployment)

---

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed (optional, for docker-compose deployment)
- Configuration file (`config.yaml`)
- Master proxy key

### Platform-Specific Installation

- **Windows 11:** See [DOCKER_WINDOWS.md](DOCKER_WINDOWS.md)
- **macOS:** Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Linux:** Install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)

---

## Quick Start

### 1. Create Configuration

```bash
# Copy template and edit
cp config_template.yaml config.yaml
# Edit config.yaml with your settings
```

### 2. Set Environment Variables

```bash
# Create .env file
cat > .env <<EOF
MOOLTIPROXY_KEY=your_secure_master_key_here
PROXY_PORT=8000
# Add any target API keys
# YOUR_OPENAI_API_KEY=sk-...
# YOUR_TGI_API_KEY=...
EOF
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

### 4. Verify

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Test endpoint
curl -H "Authorization: Bearer your_secure_master_key_here" \
     http://localhost:8000/
```

---

## Configuration

### Minimal config.yaml

```yaml
system:
  ssl: false
  debug: false
  port: 8000
  timeout: 30

cerbere:
  max_tries: 5
  whitelist: []
  blacklist: []

targets:
  default: openai

  openai:
    url: https://api.openai.com/v1
    envkey: YOUR_OPENAI_API_KEY
    mapping:
      /:
      /models:
      /completions:
      /chat/completions:
```

---

## Building the Image

### Build Manually

```bash
# Build the image
docker build -t mooltiproxy:latest .

# Build with specific tag
docker build -t mooltiproxy:1.0.0 .

# Build without cache
docker build --no-cache -t mooltiproxy:latest .
```

### Multi-platform Build

```bash
# For ARM64 and AMD64
docker buildx build --platform linux/amd64,linux/arm64 \
  -t mooltiproxy:latest .
```

---

## Running with Docker

### Basic Run

```bash
docker run -d \
  --name mooltiproxy \
  -p 8000:8000 \
  -e MOOLTIPROXY_KEY="your_secure_key" \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  mooltiproxy:latest
```

### With All Options

```bash
docker run -d \
  --name mooltiproxy \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MOOLTIPROXY_KEY="your_secure_key" \
  -e YOUR_OPENAI_API_KEY="sk-..." \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/certificates:/app/certificates:ro \
  --health-cmd="curl -f http://localhost:8000/ || exit 1" \
  --health-interval=30s \
  --health-timeout=5s \
  --health-retries=3 \
  mooltiproxy:latest
```

### Run with Debug Mode

```bash
docker run -d \
  --name mooltiproxy-debug \
  -p 8000:8000 \
  -e MOOLTIPROXY_KEY="your_secure_key" \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  mooltiproxy:latest

# View logs in real-time
docker logs -f mooltiproxy-debug
```

---

## Running with Docker Compose

### Start Services

```bash
# Start in background
docker-compose up -d

# Start in foreground (see logs)
docker-compose up

# Start and rebuild
docker-compose up -d --build
```

### Manage Services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f mooltiproxy
```

### Scale Services (if needed)

```bash
# Run multiple instances (requires load balancer)
docker-compose up -d --scale mooltiproxy=3
```

---

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `MOOLTIPROXY_KEY` | Master proxy authentication key | `my_secure_key_123` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_PORT` | Port to expose proxy on | `8000` |
| `YOUR_OPENAI_API_KEY` | OpenAI API key (if using OpenAI target) | - |
| `YOUR_TGI_API_KEY` | TGI API key (if using TGI target) | - |

### Setting Environment Variables

**Option 1: .env file (recommended)**
```bash
# Create .env file
cat > .env <<EOF
MOOLTIPROXY_KEY=my_secure_key
YOUR_OPENAI_API_KEY=sk-...
PROXY_PORT=8000
EOF
```

**Option 2: Export in shell**
```bash
export MOOLTIPROXY_KEY="my_secure_key"
export YOUR_OPENAI_API_KEY="sk-..."
```

**Option 3: Pass directly to docker-compose**
```bash
MOOLTIPROXY_KEY="my_key" docker-compose up -d
```

---

## Volume Mounts

### Configuration File (Required)

```yaml
volumes:
  - ./config.yaml:/app/config.yaml:ro
```

The `:ro` flag mounts it read-only for security.

### SSL Certificates (Optional)

If using SSL/TLS:

```yaml
volumes:
  - ./certificates:/app/certificates:ro
```

Place your `cert.pem` and `key.pem` files in the `certificates/` directory.

### Logs (Optional)

To persist logs outside container:

```yaml
volumes:
  - ./logs:/app/logs
```

---

## Health Checks

### Built-in Health Check

The Dockerfile includes a health check that curls the root endpoint:

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1
```

### Check Health Status

```bash
# Check container health
docker ps

# Detailed health info
docker inspect --format='{{json .State.Health}}' mooltiproxy | jq

# Using docker-compose
docker-compose ps
```

### Custom Health Check Endpoint

If you add a `/health` or `/__health` endpoint to the proxy:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/__health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs mooltiproxy

# Common issues:
# 1. Missing MOOLTIPROXY_KEY
docker logs mooltiproxy | grep "MOOLTIPROXY_KEY"

# 2. Invalid config.yaml
docker logs mooltiproxy | grep "Config"

# 3. Port already in use
netstat -tlnp | grep 8000
```

### Configuration Issues

```bash
# Validate config inside container
docker exec -it mooltiproxy cat /app/config.yaml

# Check if config is mounted
docker exec -it mooltiproxy ls -la /app/
```

### Permission Issues

```bash
# Check file ownership
ls -la config.yaml

# Fix permissions if needed
chmod 644 config.yaml

# Check inside container
docker exec -it mooltiproxy ls -la /app/config.yaml
```

### Network Issues

```bash
# Test from host
curl -v http://localhost:8000/

# Test from inside container
docker exec -it mooltiproxy curl http://localhost:8000/

# Check port mapping
docker port mooltiproxy
```

### Debug Mode

Run container interactively:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -e MOOLTIPROXY_KEY="test_key" \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  mooltiproxy:latest \
  /bin/bash

# Then inside container:
python -m main
```

---

## Production Deployment

### Best Practices

1. **Use Strong Keys**
   ```bash
   # Generate secure key
   openssl rand -base64 32
   ```

2. **Run Behind Reverse Proxy**

   Use nginx, Traefik, or Caddy:

   ```nginx
   # nginx example
   upstream mooltiproxy {
       server localhost:8000;
   }

   server {
       listen 443 ssl http2;
       server_name proxy.example.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://mooltiproxy;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Resource Limits**

   Add to docker-compose.yml:

   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512M
       reservations:
         cpus: '0.5'
         memory: 256M
   ```

4. **Monitoring**

   ```bash
   # Monitor resource usage
   docker stats mooltiproxy

   # Set up log forwarding
   docker-compose logs -f | tee -a proxy.log
   ```

5. **Backup Configuration**

   ```bash
   # Backup config
   cp config.yaml config.yaml.backup.$(date +%Y%m%d)
   ```

6. **Auto-restart**

   ```yaml
   restart: unless-stopped
   ```

7. **Security Scanning**

   ```bash
   # Scan image for vulnerabilities
   docker scan mooltiproxy:latest

   # Use Trivy
   trivy image mooltiproxy:latest
   ```

### Example Production docker-compose.yml

```yaml
version: '3.8'

services:
  mooltiproxy:
    build: .
    container_name: mooltiproxy-prod
    restart: unless-stopped

    ports:
      - "127.0.0.1:8000:8000"  # Only localhost

    environment:
      - MOOLTIPROXY_KEY=${MOOLTIPROXY_KEY}
      - YOUR_OPENAI_API_KEY=${YOUR_OPENAI_API_KEY}

    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 5s
      retries: 3

    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

    networks:
      - proxy-network

networks:
  proxy-network:
    driver: bridge
```

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Build image
docker-compose build

# 3. Stop old container
docker-compose stop

# 4. Start new container
docker-compose up -d

# 5. Verify
docker-compose ps
docker-compose logs -f --tail=50

# 6. Test
curl -H "Authorization: Bearer ${MOOLTIPROXY_KEY}" \
     http://localhost:8000/
```

---

## Advanced Usage

### Using with Docker Swarm

```bash
# Deploy stack
docker stack deploy -c docker-compose.yml mooltiproxy

# Scale service
docker service scale mooltiproxy_mooltiproxy=3

# Update service
docker service update --image mooltiproxy:latest mooltiproxy_mooltiproxy
```

### Using with Kubernetes

See `k8s/` directory for Kubernetes manifests (if available).

### Multi-container Setup

```yaml
# docker-compose.yml with multiple targets
version: '3.8'

services:
  proxy-openai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MOOLTIPROXY_KEY=${MOOLTIPROXY_KEY}
    volumes:
      - ./config-openai.yaml:/app/config.yaml:ro

  proxy-tgi:
    build: .
    ports:
      - "8001:8000"
    environment:
      - MOOLTIPROXY_KEY=${MOOLTIPROXY_KEY}
    volumes:
      - ./config-tgi.yaml:/app/config.yaml:ro
```

---

## Summary

Docker deployment of Mooltiproxy provides:

✅ **Consistent environment** across deployments
✅ **Easy scaling** with Docker Compose
✅ **Security** with non-root user
✅ **Health monitoring** built-in
✅ **Resource management** via Docker
✅ **Quick deployment** with docker-compose

For questions or issues, see the main README.md or open an issue on GitHub.

---

**Last Updated:** 2025-11-22
**Docker Image:** `mooltiproxy:latest`
**Base Image:** `python:3.11-slim`
