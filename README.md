
#  SwiftDeploy - Infrastructure as Code CLI Tool

A declarative infrastructure management tool that generates and manages Docker deployments from a single `manifest.yaml` file. Define your entire stack once, and SwiftDeploy handles the rest.

## Overview

Instead of manually configuring Docker, Nginx, and environment variables, SwiftDeploy lets you:
- **Define** your infrastructure in `manifest.yaml` (single source of truth)
- **Generate** all configs automatically (nginx.conf, docker-compose.yml)
- **Deploy** with confidence using pre-flight validation checks
- **Promote** between stable and canary modes without downtime
- **Test** chaos engineering scenarios to verify resilience

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- curl

### 1. Install Dependencies

```bash
pip install -r requirements-cli.txt
```

### 2. Build the Service Image

```bash
docker build -t swift-deploy-1-node:latest .
```

### 3. Deploy the Stack

```bash
./swiftdeploy deploy
```

### 4. Test the API

```bash
# Welcome endpoint
curl http://localhost:8080/

# Health check
curl http://localhost:8080/healthz
```

## Commands

### `swiftdeploy init`
Parse manifest.yaml and generate all configuration files.

```bash
./swiftdeploy init
```

Generates:
- `generated/nginx.conf` - Reverse proxy configuration
- `generated/docker-compose.yml` - Container orchestration

---

### `swiftdeploy validate`
Run 5 pre-flight checks before deployment.

```bash
./swiftdeploy validate
```

Checks:
1. manifest.yaml exists and is valid YAML
2. All required fields present and non-empty
3. Docker image referenced in manifest exists locally
4. Nginx port not already bound on host
5. Generated nginx.conf is syntactically valid

---

### `swiftdeploy deploy`
Full deployment: init → validate → docker-compose up → health checks

```bash
./swiftdeploy deploy
```

What it does:
1. Initializes configuration from manifest
2. Runs validation checks
3. Starts Docker Compose stack
4. Waits up to 60 seconds for health checks
5. Confirms both API and Nginx are healthy

---

### `swiftdeploy promote [canary|stable]`
Switch deployment mode with rolling restart (zero downtime).

```bash
# Switch to canary mode
./swiftdeploy promote canary

# Switch back to stable
./swiftdeploy promote stable
```

What it does:
1. Updates `services.mode` in manifest.yaml
2. Regenerates docker-compose.yml with new MODE env var
3. Restarts API service container only
4. Waits for health check to pass
5. Confirms mode change by checking /healthz response

---

### `swiftdeploy teardown [--clean]`
Remove all containers, networks, and volumes.

```bash
# Remove stack but keep generated configs
./swiftdeploy teardown

# Remove stack AND delete all generated configs
./swiftdeploy teardown --clean
```

---

## Configuration

### manifest.yaml - The Source of Truth

The manifest defines your entire deployment. Edit this file to change anything.

```yaml
version: "1.0"
app_name: "swift-deploy"
app_version: "1.0.0"

services:
  name: api
  image: swift-deploy-1-node:latest
  port: 3000
  mode: stable  # or canary
  restart_policy: unless-stopped
  healthcheck:
    endpoint: /healthz
    interval: 10
    timeout: 5
    retries: 3

nginx:
  image: nginx:latest
  port: 8080
  proxy_timeout: 30
  proxy_read_timeout: 30
  proxy_connect_timeout: 30

network:
  name: swiftdeploy-net
  driver_type: bridge

logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

security:
  non_root_user: appuser
  capabilities_drop:
    - ALL
  capabilities_add:
    - NET_BIND_SERVICE
```

---

## API Endpoints

### GET /
Welcome endpoint with metadata.

```bash
curl http://localhost:8080/
```

Response:
```json
{
  "message": "Welcome to SwiftDeploy API",
  "mode": "stable",
  "version": "1.0.0",
  "timestamp": "2024-04-29T20:30:45.123456Z",
  "uptime_seconds": 150
}
```

---

### GET /healthz
Health check endpoint for monitoring.

```bash
curl http://localhost:8080/healthz
```

Response:
```json
{
  "status": "healthy",
  "uptime_seconds": 150,
  "mode": "stable",
  "timestamp": "2024-04-29T20:30:45.123456Z"
}
```

---

### POST /chaos (Canary Mode Only)
Chaos engineering endpoint for testing resilience. Only available in canary mode.

#### Slow Response
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "slow", "duration": 5}'
```

#### Error Injection
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "error", "rate": 0.5}'
```

#### Recover
```bash
curl -X POST http://localhost:8080/chaos \
  -H "Content-Type: application/json" \
  -d '{"mode": "recover"}'
```

---

## Nginx Configuration

Generated `nginx.conf` includes:
- Upstream proxy to API service
- Timeouts from manifest configuration
- JSON error responses for 502/503/504
- Access logging in ISO8601 format with request timing
- Custom headers (X-Deployed-By, X-Mode)

### Access Log Format
