# HNG Stage 4A - SwiftDeploy Submission

## Project: SwiftDeploy - Infrastructure as Code CLI Tool

A declarative infrastructure management tool that generates and manages Docker deployments from a single `manifest.yaml` file.

### GitHub Repository
https://github.com/ceoemyrex/swiftdeploy

## All Requirements Met

✅ Declarative YAML manifest (manifest.yaml)
✅ CLI tool with init, validate, deploy, promote, teardown commands
✅ API service with /healthz and /chaos endpoints
✅ Nginx reverse proxy with JSON error responses
✅ Template-driven config generation (nginx.conf, docker-compose.yml)
✅ Docker multi-stage build (< 300MB)
✅ Non-root user with dropped capabilities
✅ 5-point validation system
✅ Canary deployment mode switching
✅ Health checks on both services
✅ ISO8601 access logging with request timing
✅ Chaos engineering endpoints (stable/canary modes)
✅ Complete README documentation

## Test Results

All tests passing:
- ✅ init generates correct configs
- ✅ validate runs 5 checks successfully
- ✅ deploy brings up healthy stack
- ✅ API endpoints responding (/healthz, /)
- ✅ Nginx proxying working
- ✅ Canary mode switching verified
- ✅ Chaos endpoints functional
- ✅ Containers healthy and running

## Submission Ready
